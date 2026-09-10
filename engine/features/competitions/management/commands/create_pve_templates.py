import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand


CATALOG = {
    # Debian — 8/9/10 use openstack variant from cdimage archive
    9001: {"name": "tmpl-debian8",     "url": "https://cdimage.debian.org/cdimage/openstack/archive/8.11.1/debian-8.11.1-openstack-amd64.qcow2"},
    9002: {"name": "tmpl-debian9",     "url": "https://cdimage.debian.org/cdimage/openstack/archive/9.13.0/debian-9.13.0-openstack-amd64.qcow2"},
    9003: {"name": "tmpl-debian10",    "url": "https://cdimage.debian.org/cdimage/openstack/archive/10.13.0/debian-10.13.0-openstack-amd64.qcow2"},
    9004: {"name": "tmpl-debian11",    "url": "https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-genericcloud-amd64.qcow2"},
    9005: {"name": "tmpl-debian12",    "url": "https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2"},
    # Ubuntu
    9010: {"name": "tmpl-ubuntu1404",  "url": "https://cloud-images.ubuntu.com/trusty/current/trusty-server-cloudimg-amd64-disk1.img"},
    9011: {"name": "tmpl-ubuntu1604",  "url": "https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img"},
    9012: {"name": "tmpl-ubuntu1804",  "url": "https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-amd64.img"},
    9013: {"name": "tmpl-ubuntu2204",  "url": "https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-amd64.img"},
    9014: {"name": "tmpl-ubuntu2404",  "url": "https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img"},
    # Other Linux
    9020: {"name": "tmpl-rocky9",      "url": "https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud.latest.x86_64.qcow2"},
    9021: {"name": "tmpl-opensuse155", "url": "https://download.opensuse.org/distribution/leap/15.5/appliances/openSUSE-Leap-15.5-Minimal-VM.x86_64-Cloud.qcow2"},
    9022: {"name": "tmpl-centos6",     "url": "https://cloud.centos.org/centos/6/images/CentOS-6-x86_64-GenericCloud.qcow2"},
    9023: {"name": "tmpl-centos7",     "url": "https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2"},
    9024: {"name": "tmpl-fedora31",    "url": "https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/31/Cloud/x86_64/images/Fedora-Cloud-Base-31-1.9.x86_64.qcow2"},
    9025: {"name": "tmpl-arch",        "url": "https://geo.mirror.pkgbuild.com/images/latest/Arch-Linux-x86_64-cloudimg.qcow2"},
    9026: {"name": "tmpl-alpine",      "url": "https://dl-cdn.alpinelinux.org/alpine/v3.19/releases/cloud/nocloud_alpine-3.19.1-x86_64-bios-cloudinit-r0.qcow2"},
    9027: {"name": "tmpl-almalinux",   "url": "https://repo.almalinux.org/almalinux/9/cloud/x86_64/images/AlmaLinux-9-GenericCloud-latest.x86_64.qcow2"},
    # Windows — manual ISO install required
    9040: {"name": "tmpl-winserver2016", "url": None, "note": "Install from ISO + autounattend.xml"},
    9041: {"name": "tmpl-winserver2019", "url": None, "note": "Install from ISO + autounattend.xml"},
    9042: {"name": "tmpl-winserver2022", "url": None, "note": "Install from ISO + autounattend.xml"},
    9043: {"name": "tmpl-winserver2025", "url": None, "note": "Install from ISO + autounattend.xml"},
    9044: {"name": "tmpl-win10",         "url": None, "note": "Install from ISO + autounattend.xml"},
    9045: {"name": "tmpl-win11",         "url": None, "note": "Install from ISO + autounattend.xml"},
    # Firewalls — FreeBSD, manual guest-agent setup required
    9050: {"name": "tmpl-opnsense", "url": None, "note": "Install from ISO + offline guest agent (see blog post)"},
    9051: {"name": "tmpl-pfsense",  "url": None, "note": "Install from ISO + offline guest agent (see blog post)"},
}


def build_commands(vmid, name, image_url, storage):
    filename = image_url.split("/")[-1]
    image_path = f"/var/lib/vz/template/iso/{filename}"
    return [
        f"echo '>>> [{vmid}] Downloading {name}'",
        f"wget -O {image_path} '{image_url}' 2>&1",
        f"echo '>>> [{vmid}] Installing qemu-guest-agent in image'",
        f"which virt-customize >/dev/null 2>&1 || DEBIAN_FRONTEND=noninteractive apt-get install -y libguestfs-tools 2>&1",
        f"virt-customize -a {image_path} --install qemu-guest-agent --run-command 'systemctl enable qemu-guest-agent' 2>&1",
        f"echo '>>> [{vmid}] Creating VM'",
        f"qm create {vmid} --name {name} --memory 2048 --cores 2 --net0 virtio,bridge=vmbr0 --ostype l26",
        f"echo '>>> [{vmid}] Importing disk'",
        f"qm importdisk {vmid} {image_path} {storage}",
        f"echo '>>> [{vmid}] Configuring'",
        f"qm set {vmid} --scsihw virtio-scsi-pci --scsi0 {storage}:vm-{vmid}-disk-0",
        f"qm set {vmid} --ide2 {storage}:cloudinit",
        f"qm set {vmid} --boot c --bootdisk scsi0",
        f"qm set {vmid} --serial0 socket --vga serial0",
        f"qm set {vmid} --agent enabled=1",
        f"echo '>>> [{vmid}] Converting to template'",
        f"qm template {vmid}",
        f"echo '>>> [{vmid}] Done'",
    ]


class Command(BaseCommand):
    help = "SSH into PVE and create cloud-init VM templates for all Linux entries in the catalog."

    def add_arguments(self, parser):
        parser.add_argument("--vmids", nargs="+", type=int,
            help="Only create these VMIDs. Default: all cloud-init templates.")
        parser.add_argument("--dry-run", action="store_true",
            help="Print the commands that would run without executing them.")
        parser.add_argument("--force", action="store_true",
            help="Destroy and recreate templates that already exist on PVE.")
        parser.add_argument("--storage", default=None,
            help="PVE storage name (default: PROXMOX_STORAGE env var or 'local-lvm').")

    def handle(self, *args, **options):
        try:
            import paramiko
        except ImportError:
            self.stderr.write(self.style.ERROR("paramiko is required: pip install paramiko"))
            return

        config = settings.PROXMOX
        host = config["host"]
        ssh_user = os.getenv("PROXMOX_SSH_USER", "root")
        ssh_password = os.getenv("PROXMOX_SSH_PASSWORD")
        ssh_key = os.getenv("PROXMOX_SSH_KEY_PATH")
        storage = options["storage"] or os.getenv("PROXMOX_STORAGE", "local-lvm")
        dry_run = options["dry_run"]
        force = options["force"]

        if not host:
            self.stderr.write(self.style.ERROR("PROXMOX_HOST is not set in .env"))
            return

        target_vmids = options["vmids"] or list(CATALOG.keys())
        targets = {vmid: CATALOG[vmid] for vmid in target_vmids if vmid in CATALOG}

        automatable = {vmid: t for vmid, t in targets.items() if t.get("url")}
        manual = {vmid: t for vmid, t in targets.items() if not t.get("url")}

        if manual:
            self.stdout.write(self.style.WARNING("\nSkipped (manual install required):"))
            for vmid, t in manual.items():
                self.stdout.write(f"  VMID {vmid:5d}  {t['name']:28s}  {t.get('note', '')}")

        if not automatable:
            self.stdout.write("No cloud-init templates to create.")
            return

        self.stdout.write(f"\nTarget: {host}  storage: {storage}  user: {ssh_user}")
        self.stdout.write(f"Templates to create: {len(automatable)}\n")

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN — commands that would execute:\n"))
            for vmid, t in automatable.items():
                for cmd in build_commands(vmid, t["name"], t["url"], storage):
                    self.stdout.write(f"  {cmd}")
                self.stdout.write("")
            return

        # Connect
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            connect_kwargs = {"username": ssh_user, "timeout": 10}
            if ssh_key:
                connect_kwargs["key_filename"] = ssh_key
            elif ssh_password:
                connect_kwargs["password"] = ssh_password
            else:
                self.stderr.write(self.style.ERROR(
                    "Set PROXMOX_SSH_PASSWORD or PROXMOX_SSH_KEY_PATH in .env"
                ))
                return
            ssh.connect(host, **connect_kwargs)
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"SSH connection failed: {exc}"))
            return

        # Check existing VMIDs
        if not force:
            _, stdout, _ = ssh.exec_command("qm list | awk 'NR>1 {print $1}'")
            existing = {int(l.strip()) for l in stdout if l.strip().isdigit()}
            already = {vmid: t for vmid, t in automatable.items() if vmid in existing}
            automatable = {vmid: t for vmid, t in automatable.items() if vmid not in existing}
            if already:
                self.stdout.write(self.style.WARNING("Already on PVE (use --force to recreate):"))
                for vmid, t in already.items():
                    self.stdout.write(f"  VMID {vmid}  {t['name']}")
                self.stdout.write("")

        if not automatable:
            self.stdout.write("Nothing to create.")
            ssh.close()
            return

        succeeded, failed = [], []

        for vmid, t in automatable.items():
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n[{vmid}] {t['name']}"))

            if force:
                _, out, _ = ssh.exec_command(
                    f"qm stop {vmid} --skiplock 1 2>/dev/null; qm destroy {vmid} --purge 1 2>/dev/null; echo done",
                    timeout=60,
                )
                out.channel.recv_exit_status()

            full_script = "{ " + " && ".join(build_commands(vmid, t["name"], t["url"], storage)) + "; } 2>&1"
            _, stdout, _ = ssh.exec_command(full_script, timeout=600)

            output_lines = []
            for line in stdout:
                line = line.rstrip()
                self.stdout.write(f"  {line}")
                output_lines.append(line)

            exit_status = stdout.channel.recv_exit_status()
            if exit_status == 0:
                self.stdout.write(self.style.SUCCESS(f"  [OK] {t['name']}"))
                succeeded.append(vmid)
            else:
                self.stderr.write(self.style.ERROR(f"  [FAILED] {t['name']} (exit {exit_status})"))
                failed.append(vmid)

        ssh.close()

        self.stdout.write(self.style.MIGRATE_HEADING("\n--- Summary ---"))
        self.stdout.write(self.style.SUCCESS(f"  Created:  {len(succeeded)}"))
        if failed:
            self.stdout.write(self.style.ERROR(f"  Failed:   {len(failed)} — VMIDs {failed}"))
        if manual:
            self.stdout.write(self.style.WARNING(f"  Skipped (manual): {len(manual)}"))
