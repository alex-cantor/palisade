import time

from django.conf import settings
from django.contrib.auth.models import User

from features.competitions.models import ProvisionedMachine
from features.teams.models import Team, TeamMember


def provision_teams(competition, num_teams, username_prefix, default_password):
  teams = []

  for team_number in range(1, num_teams + 1):
    team_name = f"Team {team_number}"

    team, _ = Team.objects.get_or_create(
      competition=competition,
      name=team_name,
    )

    # Create a default member account if none exists yet
    if not team.members.exists():
      username = f"{username_prefix}{team_number}"
      user, created = User.objects.get_or_create(username=username)
      if created:
        user.set_password(default_password)
        user.save(update_fields=["password"])

      TeamMember.objects.get_or_create(user=user, team=team)

    teams.append(team)

  return teams


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
    )
  except Exception as exc:
    return {"status": "error", "detail": f"Could not connect to ProxMox: {exc}"}

  provisioned = []
  errors = []

  for team_number, team in enumerate(teams, start=1):
    vm_offset = 0

    # Use first member's credentials for cloud-init, fall back to team name slug
    first_member = team.members.select_related("user").first()
    ci_user = first_member.user.username if first_member else f"team{team_number}"

    for machine in machines:
      template = machine.machine_template

      if not template.proxmox_vmid:
        errors.append(
          f"Template '{template.name}' has no ProxMox VMID — set it in Templates before provisioning."
        )
        continue

      machine_slug = (template.role or template.name).lower().replace(" ", "-")

      for instance_number in range(1, machine.quantity + 1):
        vmid = 50000 + team_number * 100 + vm_offset
        vm_name = f"t{team_number}-{machine_slug}-{instance_number}"

        try:
          clone_task = (
            proxmox.nodes(node)
            .qemu(template.proxmox_vmid)
            .clone.post(newid=vmid, name=vm_name, full=1, target=node)
          )
          wait_for_proxmox_task(proxmox, node, clone_task)

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
