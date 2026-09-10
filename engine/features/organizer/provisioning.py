import random
import threading
import time
import uuid

from django.conf import settings
from django.contrib.auth.models import User

from features.competitions.models import ProvisionedMachine
from features.teams.models import Team, TeamMember

_ADJECTIVES = [
  "amber", "azure", "bold", "brave", "bright", "calm", "clean", "clear",
  "clever", "crisp", "dark", "deft", "eager", "early", "faint", "fast",
  "fierce", "fleet", "fresh", "grand", "great", "green", "harsh", "heavy",
  "hollow", "icy", "jolly", "keen", "large", "lean", "light", "lofty",
  "lunar", "mellow", "mighty", "noble", "nimble", "pale", "plain", "polar",
  "prime", "proud", "quick", "quiet", "rapid", "raw", "remote", "rocky",
  "rough", "royal", "rusty", "sharp", "shiny", "silent", "sleek", "slim",
  "slow", "small", "smart", "solar", "spare", "stark", "stern", "stoic",
  "stout", "strong", "subtle", "swift", "tall", "terse", "thin", "tidy",
  "tight", "tough", "trim", "true", "vast", "vivid", "warm", "wild", "wise",
]

_NOUNS = [
  "ash", "bat", "bay", "bear", "bee", "birch", "bison", "boar", "bolt",
  "buck", "cliff", "cloud", "crane", "crow", "deer", "delta", "dove",
  "drift", "dusk", "eagle", "echo", "elk", "ember", "falcon", "fern",
  "flint", "fog", "forge", "fox", "frost", "gale", "gust", "hawk", "haze",
  "helm", "heron", "hound", "ibis", "iris", "jade", "jaguar", "kite",
  "lance", "lark", "lava", "leaf", "ledge", "lion", "lynx", "marsh",
  "mist", "mole", "moon", "moose", "moth", "mule", "newt", "oak", "owl",
  "peak", "pike", "pine", "puma", "quail", "raven", "reef", "ridge",
  "rook", "rune", "sage", "seal", "shard", "shore", "slate", "sparrow",
  "spire", "stag", "star", "stone", "storm", "swan", "talon", "thorn",
  "tide", "tiger", "toad", "torch", "vale", "vapor", "viper", "vole",
  "wasp", "wave", "wind", "wolf", "wren", "yak", "zephyr",
]

def _random_name():
  return f"{random.choice(_ADJECTIVES)}-{random.choice(_NOUNS)}"


# ---------------------------------------------------------------------------
# Background job tracking
# ---------------------------------------------------------------------------

_JOBS: dict = {}
_JOBS_LOCK = threading.Lock()


def _new_job() -> str:
  job_id = str(uuid.uuid4())
  with _JOBS_LOCK:
    _JOBS[job_id] = {"done": False, "success": None, "log": [], "final": ""}
  return job_id


def _job_log(job_id: str, level: str, text: str):
  with _JOBS_LOCK:
    if job_id in _JOBS:
      _JOBS[job_id]["log"].append({"level": level, "text": text})


def _job_finish(job_id: str, success: bool, final: str):
  with _JOBS_LOCK:
    if job_id in _JOBS:
      _JOBS[job_id].update({"done": True, "success": success, "final": final})


def get_job_status(job_id: str) -> dict | None:
  with _JOBS_LOCK:
    job = _JOBS.get(job_id)
    if not job:
      return None
    return {
      "done": job["done"],
      "success": job["success"],
      "log": list(job["log"]),
      "final": job["final"],
    }


# ---------------------------------------------------------------------------
# Teams
# ---------------------------------------------------------------------------

def provision_teams(competition, num_teams, username_prefix, default_password):
  teams = []

  for team_number in range(1, num_teams + 1):
    team_name = f"Team {team_number}"

    team, _ = Team.objects.get_or_create(
      competition=competition,
      name=team_name,
    )

    if not team.members.exists():
      username = f"{username_prefix}{team_number}"
      user, created = User.objects.get_or_create(username=username)
      if created:
        user.set_password(default_password)
        user.save(update_fields=["password"])

      TeamMember.objects.get_or_create(user=user, defaults={"team": team})

    teams.append(team)

  return teams


# ---------------------------------------------------------------------------
# PVE helpers
# ---------------------------------------------------------------------------

def wait_for_proxmox_task(proxmox, node, task_id, timeout=300):
  deadline = time.monotonic() + timeout

  while time.monotonic() < deadline:
    task = proxmox.nodes(node).tasks(task_id).status.get()

    if task["status"] == "stopped":
      exit_status = task.get("exitstatus")
      if exit_status == "OK":
        return
      raise RuntimeError(f"ProxMox task failed: {exit_status}")

    time.sleep(3)

  raise TimeoutError(f"Task {task_id} did not complete within {timeout}s")


def _ssh_grow_disk(host, vmid):
  """SSH to PVE and grow the last partition + filesystem to fill the resized LV.
  Detects the last partition number dynamically so it works with cloud images
  that have multiple partitions (BIOS boot / EFI / root)."""
  import os
  import paramiko

  ssh_user = os.getenv("PROXMOX_SSH_USER", "root")
  ssh_password = os.getenv("PROXMOX_SSH_PASSWORD")
  ssh_key = os.getenv("PROXMOX_SSH_KEY_PATH")

  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  connect_kwargs = {"username": ssh_user, "timeout": 10}
  if ssh_key:
    connect_kwargs["key_filename"] = ssh_key
  elif ssh_password:
    connect_kwargs["password"] = ssh_password
  else:
    raise RuntimeError("No SSH credentials configured")

  ssh.connect(host, **connect_kwargs)

  # 1. sgdisk -e: moves the GPT backup partition table to the true end of the
  #    disk after the LV was resized. Without this, GRUB/UEFI sees a corrupt
  #    partition table and the VM fails to boot (io-error). Harmless on MBR.
  # 2. parted resizepart: extends the last (root) partition to fill the disk.
  #    Cloud-init's growroot then resizes the filesystem on first boot.
  # No losetup — it can hang if the LV is still hot after a resize.
  dev = f"/dev/pve/vm-{vmid}-disk-0"
  cmd = (
    f"sgdisk -e {dev} 2>/dev/null || true; "
    f"LAST=$(parted -s {dev} print 2>/dev/null | awk '/^ *[0-9]/{{n=$1}} END{{print n}}'); "
    f"[ -n \"$LAST\" ] && parted -s {dev} resizepart \"$LAST\" 100% 2>/dev/null || true; "
    f"true"
  )
  _, stdout, _ = ssh.exec_command(cmd, timeout=30)
  stdout.channel.recv_exit_status()
  ssh.close()


def _api_set_vm_password(proxmox, node, vmid, username, password, log_fn=None):
  def _log(msg):
    if log_fn:
      log_fn(msg)

  import base64

  # Wait up to 5 minutes — Ubuntu cloud-init can take 3+ minutes before the
  # guest agent becomes reachable. Retry every 15 s, 20 attempts = 5 min.
  max_retries = 20
  for attempt in range(max_retries):
    # ── Primary: agent set-user-password (clean, no shell needed) ────────────
    try:
      proxmox.nodes(node).qemu(vmid).agent("set-user-password").post(
        username=username,
        password=password,
      )
      _log(f"Password set via guest agent (attempt {attempt + 1}).")
      return True
    except Exception as exc:
      err = str(exc)
      agent_down = "not running" in err.lower() or "500" in err or "agent" in err.lower()
      if not agent_down:
        # Agent is up but set-user-password failed — most likely because
        # cloud-init's ciuser didn't create the user (happens on Ubuntu when
        # the username conflicts with an existing system group like 'admin').
        # Ensure the user exists, then set the password via chpasswd.
        _log(f"set-user-password failed ({exc}), ensuring user exists and retrying…")
        try:
          b64 = base64.b64encode(f"{username}:{password}\n".encode()).decode()
          script = (
            # Create user if missing. If a group with the same name already
            # exists (e.g. 'admin' on Debian/Ubuntu), reuse it with -g.
            f"if ! id {username} >/dev/null 2>&1; then "
            f"  if getent group {username} >/dev/null 2>&1; then "
            f"    useradd -m -s /bin/bash -g {username} -G sudo {username}; "
            f"  else "
            f"    useradd -m -s /bin/bash -G sudo {username} 2>/dev/null || "
            f"    useradd -m -s /bin/bash {username}; "
            f"  fi; "
            f"fi; "
            f"echo {b64} | base64 -d | chpasswd; "
            f"passwd -u {username} 2>/dev/null || true"
          )
          exec_res = proxmox.nodes(node).qemu(vmid).agent("exec").post(**{
            "command": ["bash", "-c", script]
          })
          pid = exec_res.get("pid")
          if pid:
            for _ in range(15):
              time.sleep(1)
              status = proxmox.nodes(node).qemu(vmid).agent("exec-status").get(pid=pid)
              if status.get("exited"):
                if status.get("exitcode", 1) == 0:
                  _log(f"User created and password set via exec fallback (attempt {attempt + 1}).")
                  return True
                _log(f"exec fallback exited {status.get('exitcode')}: {status.get('err-data', '')}")
                break
        except Exception as exc2:
          _log(f"exec fallback also failed: {exc2}")
        return False

    if attempt < max_retries - 1:
      _log(f"Guest agent not ready yet, retrying in 15 s… ({attempt + 1}/{max_retries})")
      time.sleep(15)

  _log("Guest agent never became available — cloud-init credentials will apply instead.")
  return False


def _ssh_force_destroy(host, vmid):
  """SSH into PVE and forcefully remove a VM — last resort for broken VMs."""
  import os
  import paramiko

  ssh_user = os.getenv("PROXMOX_SSH_USER", "root")
  ssh_password = os.getenv("PROXMOX_SSH_PASSWORD")
  ssh_key = os.getenv("PROXMOX_SSH_KEY_PATH")

  ssh = paramiko.SSHClient()
  ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
  connect_kwargs = {"username": ssh_user, "timeout": 10}
  if ssh_key:
    connect_kwargs["key_filename"] = ssh_key
  elif ssh_password:
    connect_kwargs["password"] = ssh_password
  else:
    raise RuntimeError("No SSH credentials (PROXMOX_SSH_PASSWORD or PROXMOX_SSH_KEY_PATH)")

  ssh.connect(host, **connect_kwargs)
  cmd = "\n".join([
    f"qm stop {vmid} --skiplock 1 2>/dev/null",
    f"sleep 2",
    f"pid=$(cat /var/run/qemu-server/{vmid}.pid 2>/dev/null); [ -n \"$pid\" ] && kill -9 $pid 2>/dev/null; sleep 1",
    f"qm destroy {vmid} --purge 1 --skiplock 1 2>/dev/null",
    f"rm -f /etc/pve/qemu-server/{vmid}.conf",
    f"lvs --noheadings -o lv_name 2>/dev/null | grep 'vm-{vmid}-' | xargs -I{{}} lvremove -f pve/{{}} 2>/dev/null",
    "true",
  ])
  _, stdout, _ = ssh.exec_command(cmd)
  stdout.channel.recv_exit_status()
  ssh.close()


# ---------------------------------------------------------------------------
# Baseline provision
# ---------------------------------------------------------------------------

def provision_baseline(competition, log=None):
  """Phase 1: clone all configured machine templates once for Team 1."""
  from proxmoxer import ProxmoxAPI

  def L(level, text):
    if log:
      log(level, text)

  config = settings.PROXMOX
  node = config["node"]
  bridge = config["bridge"]

  machines = list(competition.machines.select_related("machine_template"))
  if not machines:
    return {"status": "error", "detail": "No machines configured — add templates to this competition first."}

  team = competition.teams.order_by("name").first()
  if not team:
    return {"status": "error", "detail": "No teams provisioned yet — run team provisioning first."}

  missing = [m.machine_template.name for m in machines if not m.machine_template.proxmox_vmid]
  if missing:
    return {
      "status": "error",
      "detail": f"These templates have no ProxMox VMID set: {', '.join(missing)}.",
    }

  L("info", "Connecting to PVE...")
  try:
    proxmox = ProxmoxAPI(
      config["host"],
      user=config["user"],
      token_name=config["token_name"],
      token_value=config["token_value"],
      verify_ssl=config["verify_ssl"],
      timeout=30,
    )
  except Exception as exc:
    return {"status": "error", "detail": f"Could not connect to ProxMox: {exc}"}

  L("info", "Verifying templates exist on PVE...")
  existing_vmids = {vm["vmid"] for vm in proxmox.nodes(node).qemu.get()}
  not_found = [m.machine_template.name for m in machines if m.machine_template.proxmox_vmid not in existing_vmids]
  if not_found:
    return {
      "status": "error",
      "detail": f"Template VMIDs not found on PVE node '{node}': {', '.join(not_found)}.",
    }

  provisioned = []
  errors = []
  vm_offset = 0

  for machine in machines:
    template = machine.machine_template

    for instance_number in range(1, machine.quantity + 1):
      vmid = 49000 + vm_offset
      vm_name = f"baseline-{_random_name()}"

      if ProvisionedMachine.objects.filter(vmid=vmid).exists():
        vm_offset += 1
        continue

      # Clean up stale PVE state before cloning
      L("info", f"Clearing any stale state at VMID {vmid}...")
      try:
        stop_task = proxmox.nodes(node).qemu(vmid).status.stop.post(skiplock=1)
        if stop_task:
          wait_for_proxmox_task(proxmox, node, stop_task)
        else:
          time.sleep(3)
      except Exception:
        pass
      api_deleted = False
      try:
        del_task = proxmox.nodes(node).qemu(vmid).delete(purge=1)
        if del_task:
          wait_for_proxmox_task(proxmox, node, del_task)
        else:
          time.sleep(2)
        api_deleted = True
      except Exception:
        pass
      if not api_deleted:
        try:
          _ssh_force_destroy(config["host"], vmid)
        except Exception:
          pass

      try:
        L("info", f"Cloning {template.name} as {vm_name} (VMID {vmid})...")
        clone_task = (
          proxmox.nodes(node)
          .qemu(template.proxmox_vmid)
          .clone.post(newid=vmid, name=vm_name, full=1, target=node)
        )
        wait_for_proxmox_task(proxmox, node, clone_task, timeout=1800)

        baseline_password = getattr(settings, "PROXMOX_BASELINE_PASSWORD", "palisade")
        ci_user = template.default_user or "admin"

        L("info", f"Configuring network + credentials for {vm_name}...")
        proxmox.nodes(node).qemu(vmid).config.post(
          ipconfig0="ip=dhcp",
          net0=f"virtio,bridge={bridge}",
          ciuser=ci_user,
          cipassword=baseline_password,
        )

        L("info", f"Resizing disk to 40 GB...")
        proxmox.nodes(node).qemu(vmid).resize.put(disk="scsi0", size="40G")

        L("info", f"Starting {vm_name}...")
        start_task = proxmox.nodes(node).qemu(vmid).status.start.post()
        if start_task:
          wait_for_proxmox_task(proxmox, node, start_task)

        # Verify PVE didn't immediately error (e.g. thin pool full → io-error)
        time.sleep(8)
        vm_status = proxmox.nodes(node).qemu(vmid).status.current.get()
        actual_status = vm_status.get("status", "unknown")
        if actual_status != "running":
          raise RuntimeError(
            f"VM started but PVE reports status='{actual_status}'. "
            f"Check PVE console for VMID {vmid}. "
            f"Run on PVE: lvs -o lv_name,data_percent pve | grep data"
          )

        ProvisionedMachine.objects.create(
          competition=competition,
          team=team,
          machine_template=template,
          vmid=vmid,
          name=vm_name,
          status="running",
        )

        L("info", f"Waiting for guest agent to set password for {vm_name}…")
        _api_set_vm_password(
          proxmox, node, vmid, ci_user, baseline_password,
          log_fn=lambda msg: L("info", msg),
        )

        try:
          ifaces = proxmox.nodes(node).qemu(vmid).agent("network-get-interfaces").get()
          ip = next(
            addr["ip-address"]
            for iface in ifaces.get("result", [])
            if iface.get("name") != "lo"
            for addr in iface.get("ip-addresses", [])
            if addr.get("ip-address-type") == "ipv4"
          )
          ProvisionedMachine.objects.filter(vmid=vmid).update(ip_address=ip)
          L("info", f"{vm_name} IP: {ip}")
        except Exception:
          L("info", f"Could not determine IP for {vm_name} — set it manually in admin.")

        L("success", f"{vm_name} ready — login: {ci_user} / {baseline_password}")
        L("info", "Serial console login prompt is normal — cloud-init may still be finishing.")
        provisioned.append({"vmid": vmid, "name": vm_name})
        vm_offset += 1

      except Exception as exc:
        L("error", f"{vm_name} (VMID {vmid}): {exc}")
        errors.append(f"[VMID {vmid}] {vm_name}: {exc}")
        vm_offset += 1

  if not errors:
    status = "done"
  elif provisioned:
    status = "partial"
  else:
    status = "error"

  return {"status": status, "provisioned": provisioned, "errors": errors}


def provision_baseline_bg(competition) -> str:
  """Start provision_baseline in a background thread. Returns a job_id to poll."""
  job_id = _new_job()

  def run():
    _job_log(job_id, "info", "Starting baseline provision...")
    result = provision_baseline(competition, log=lambda level, text: _job_log(job_id, level, text))
    if result["status"] == "done":
      n = len(result["provisioned"])
      _job_finish(job_id, True, f"{n} VM(s) provisioned successfully.")
    elif result["status"] == "partial":
      n = len(result["provisioned"])
      errs = "; ".join(result["errors"])
      _job_finish(job_id, False, f"{n} VM(s) provisioned, but errors occurred: {errs}")
    else:
      _job_finish(job_id, False, result.get("detail") or "; ".join(result.get("errors", ["Unknown error"])))

  threading.Thread(target=run, daemon=True).start()
  return job_id


# ---------------------------------------------------------------------------
# Baseline deprovision
# ---------------------------------------------------------------------------

def deprovision_baseline(competition, log=None):
  """Delete all baseline VMs (VMID 49000–49999) from PVE and the DB.
  Only removes a DB record once PVE confirms the VM is gone."""
  from proxmoxer import ProxmoxAPI

  def L(level, text):
    if log:
      log(level, text)

  baseline_vms = list(
    competition.provisioned_machines.filter(vmid__gte=49000, vmid__lte=49999)
  )
  if not baseline_vms:
    return {"status": "error", "detail": "No baseline VMs found for this competition."}

  config = settings.PROXMOX
  host = config["host"]
  errors = []
  deleted = 0

  L("info", "Connecting to PVE...")
  try:
    proxmox = ProxmoxAPI(
      host,
      user=config["user"],
      token_name=config["token_name"],
      token_value=config["token_value"],
      verify_ssl=config["verify_ssl"],
      timeout=30,
    )
    node = config["node"]
  except Exception as exc:
    return {"status": "error", "detail": f"Could not connect to PVE: {exc}"}

  for vm in baseline_vms:
    pve_ok = False

    L("info", f"Stopping {vm.name} (VMID {vm.vmid})...")
    try:
      stop_task = proxmox.nodes(node).qemu(vm.vmid).status.stop.post(skiplock=1)
      if stop_task:
        wait_for_proxmox_task(proxmox, node, stop_task, timeout=60)
      else:
        time.sleep(3)
    except Exception:
      pass  # already stopped or doesn't exist on PVE — continue to delete

    L("info", f"Deleting {vm.name} (VMID {vm.vmid})...")
    try:
      del_task = proxmox.nodes(node).qemu(vm.vmid).delete(purge=1)
      if del_task:
        wait_for_proxmox_task(proxmox, node, del_task, timeout=120)
      pve_ok = True
    except Exception as exc:
      L("warning", f"API delete failed for {vm.name}, trying SSH fallback...")
      try:
        _ssh_force_destroy(host, vm.vmid)
        pve_ok = True
      except Exception as ssh_exc:
        L("error", f"Could not delete {vm.name}: {ssh_exc}")
        errors.append(f"[VMID {vm.vmid}] {vm.name}: {ssh_exc}")

    if pve_ok:
      L("success", f"{vm.name} deleted")
      vm.delete()
      deleted += 1

  if not errors:
    return {"status": "done", "deleted": deleted}
  return {"status": "partial", "deleted": deleted, "errors": errors}


def deprovision_baseline_bg(competition) -> str:
  """Start deprovision_baseline in a background thread. Returns a job_id to poll."""
  job_id = _new_job()

  def run():
    _job_log(job_id, "info", "Starting baseline deletion...")
    result = deprovision_baseline(competition, log=lambda level, text: _job_log(job_id, level, text))
    if result["status"] == "done":
      _job_finish(job_id, True, f"{result['deleted']} VM(s) deleted.")
    elif result["status"] == "partial":
      errs = "; ".join(result.get("errors", []))
      _job_finish(job_id, False, f"{result['deleted']} deleted, errors: {errs}")
    else:
      _job_finish(job_id, False, result.get("detail", "Unknown error"))

  threading.Thread(target=run, daemon=True).start()
  return job_id


# ---------------------------------------------------------------------------
# Full infrastructure provision
# ---------------------------------------------------------------------------

def provision_infrastructure(competition):
  from proxmoxer import ProxmoxAPI

  config = settings.PROXMOX
  node = config["node"]
  bridge = config["bridge"]

  teams = list(competition.teams.all())
  machines = list(competition.machines.select_related("machine_template"))

  if not teams:
    return {"status": "error", "detail": "No teams provisioned yet — run team provisioning first."}

  if not machines:
    return {"status": "error", "detail": "No machines configured for this competition."}

  try:
    proxmox = ProxmoxAPI(
      config["host"],
      user=config["user"],
      token_name=config["token_name"],
      token_value=config["token_value"],
      verify_ssl=config["verify_ssl"],
      timeout=30,
    )
  except Exception as exc:
    return {"status": "error", "detail": f"Could not connect to ProxMox: {exc}"}

  provisioned = []
  errors = []

  for team_number, team in enumerate(teams, start=1):
    vm_offset = 0

    first_member = team.members.select_related("user").first()
    ci_user = first_member.user.username if first_member else f"team{team_number}"

    for machine in machines:
      template = machine.machine_template

      if not template.proxmox_vmid:
        errors.append(f"Template '{template.name}' has no ProxMox VMID.")
        continue

      for instance_number in range(1, machine.quantity + 1):
        vmid = 50000 + team_number * 100 + vm_offset
        vm_name = f"t{team_number}-{_random_name()}"

        try:
          clone_task = (
            proxmox.nodes(node)
            .qemu(template.proxmox_vmid)
            .clone.post(newid=vmid, name=vm_name, full=1, target=node)
          )
          wait_for_proxmox_task(proxmox, node, clone_task, timeout=1800)

          vm = proxmox.nodes(node).qemu(vmid)
          vm.config.post(
            ciuser=ci_user,
            cipassword=first_member.user.username if first_member else f"team{team_number}",
            ipconfig0="ip=dhcp",
            net0=f"virtio,bridge={bridge}",
          )
          vm.status.start.post()

          ProvisionedMachine.objects.create(
            competition=competition,
            team=team,
            machine_template=template,
            vmid=vmid,
            name=vm_name,
            status="running",
          )

          provisioned.append({"vmid": vmid, "name": vm_name, "team": team.name})
          vm_offset += 1

        except Exception as exc:
          errors.append(f"[VMID {vmid}] {vm_name}: {exc}")

  if not errors:
    status = "done"
  elif provisioned:
    status = "partial"
  else:
    status = "error"

  return {"status": status, "provisioned": provisioned, "errors": errors}
