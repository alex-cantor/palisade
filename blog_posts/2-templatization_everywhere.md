# Palisade: Templatization Everywhere (part 2)

## Initial Ideation

The first step of the project--the main engine of the tool--is the mock environment generator. So, what does that consist of? Spawning VMs and injecting vulnerabilities, mostly. So, let’s take a look at spawning VMs.

There are two main ways we can spawn VMs in ProxMox (PVE): we can build them from the iso, or we can clone an existing VM. Cloning an existing VM is much easier: we don’t need to script building the VMs, and it is super reliable. For our purposes, we’ll clone from a template, which is functional and ready for our use.

> Disclosure: this stuff has not been tested. A lot of it was pieced together by my logs, as this was done through lots of iteration (failure -> learn something-> try again). It is meant to serve as a guide and a learning opportunity for both you and me; if you test it yourself, let me know and I will update and credit as appropriate.

## Choosing OSs to Clone

I knew I wanted to be able to prepare my team for anything, from old to new, from common to esoteric. So, I formed a list of the following OSs/distros which I wanted to make a template of (templatize):

**Linux**
- Debian
- Debian 8
- Debian 9
- Debian 10
- Debian 11
- Debian 12
- Ubuntu
- Ubuntu 14.04
- Ubuntu 16.04
- Ubuntu 18.04
- Ubuntu 22.04
- Ubuntu 24.04
- Rocky Linux 9
- openSUSE Leap 15.5
- CentOS
	- CentOS 6
	- CentOS 7
- Fedora 31
- Arch Linux
- Alpine Linux
- AlmaLinux

**Windows**
- Windows Server
	- Windows Server 2016
	- Windows Server 2019
	- Windows Server 2022
	- Windows Server 2025
- Windows
	- Windows 10
	- Windows 11

**Firewalling**
- OPNsense
- pfSense

## Creating the Templates

This process was a good bit annoying (especially for Windows, not so much for Linux, only a little bit for FreeBSD)--but I did learn a ton, so I guess it all evened out in the end.

### Linux
Creating the VMs here was insanely easy. You may have noticed I gave you URLs. Those are current (at the time of posting this) mirrors of the cloud images of each OS/distro. We can then use a tool called cloud-init to quickly create the VMs. Here’s what that looks like for Debian 12:
```bash
cd /var/lib/vz/template/iso
wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2
qm create 9001 --name tmpl-debian12 --memory 2048 --cores 2 --net0 virtio,bridge=umd_lan1
qm importdisk 9001 debian-12-genericcloud-amd64.qcow2 UMD-CCDC-Disk
qm set 9001 --scsihw virtio-scsi-pci --scsi0 UMD-CCDC-Disk:vm-9001-disk-0
qm set 9001 --ide2 UMD-CCDC-Disk:cloudinit
qm set 9001 --boot c --bootdisk scsi0
qm set 9001 --serial0 socket --vga serial0
qm set 9001 --agent enabled=1
qm template 9001
```

Let’s break down what each command is doing.
1. `wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2` - this simply downloads the qcow2 file from Debian’s website. `wget` is the tool that does the downloading; while there are other tools (such as `curl`), wget does a nice job at getting it done
2. `qm create 9001 --name tmpl-debian12 --memory 2048 --cores 2 --net0 virtio,bridge=umd_lan1` - now we are getting into more advanced commands, although this is still quite simple. `qm` is a built-in tool in PVE which is incredibly valuable for managing VMs. Here, we use it to create a VM with the ID 9001, the name tmpl-debian12, 2048 MB (2 GB) of memory, two CPU cores, and configures the first network adapter (net0) to use the VirtIO paravirtualized network driver (which is very performant), and bridges the network driver to the umd_lan1 (the name of the lan I called this)
3. `qm set 9001 --scsihw virtio-scsi-pci --scsi0 UMD-CCDC-Disk:vm-9001-disk-0` - this sets the SCSI controller hardware type to VirtIO SCSI PCE (a high-performance storage controller standard for PVE), and attaches a specific virtual disk to the VM’s first SCSI slot (scsi0) (on the UMD-CCDC-Disk storage pool it is the disk of name vm-9001-disk-0. This name is important--if it is not in that format, PVE may be confused I want to test it)
4. `qm set 9001 --ide2 UMD-CCDC-Disk:cloudinit` - `--ide2` specifies the cloud-init drive should be on IDE2 interface slot (IDE because it is universally compatible so you don’t need special VirtIO drivers); `UMD-CCDC-Disk:cloudinit` tells PVE to generate a special cloudinit iso on UMD-CCDC-Disk
5. `qm set 9001 --boot c --bootdisk scsi0` - here, we set the C drive as the first hard drive and attach scsi0 to the first hard drive (how does step 5 relate to step 3?)
> Aside: C is traditionally the first hard drive, as A and B were reserved for floppy drives (on early IBM PCs)
6. `qm set 9001 --serial0 socket --vga serial0` - `--serial0 socket` creates a virtual serial port for the VM (so PVE can connect right to the VM’s serial stream); `--vga serial0` redirects the VGA output to the socket in the previous flag
7. `qm set 9001 --agent enabled=1` - this simply enables the guest-agent feature, which enables a ton of configuration abilities.
8. `qm template 9001` - this does the final templatization, so it is all ready to clone! at this point, we can’t interact with the VM until is is cloned

### Windows

Windows was really annoying. The TL;DR here is that you can use autounattend.xml and unattend.xml for a speedy setup--but I did not know about those things originally. I am moving on at this point (as I have been working on the templatization + writeup for a few weeks now), but I will come back eventually.

### FreeBSD (OPNsense and pfSense)
“Alrighty,” I thought. “I am finally done breaking these VMs and qemu will work perfectly.” Haha, I think now. For that was far from the truth.

The first thing I did was get both the pfSense and OPNsense ISOs turned to VMs. That didn’t give me any trouble:

It was then time to deal with the qemu guest agent stuff, which I was hoping wouldn’t give me too much trouble.
1. Enable the agent in ProxMox
```bash
qm set <VMID> --agent 1
```
2. Install the agent in pfSense
a. Log into pfSense
```text
login: opnsense
password: <enter your password>
```
b. Get through the wizard
i. Should VLANs be set up now? n
ii. Enter the WAN interface name or ‘a’ for auto-detection: vtnet0
iii Enter the LAN interface name or ‘a’ for auto-detection (or nothing if finished): [Enter]
iv Do you want to proceed? y
c. Get in that shell
```text
Select `Option 8) Shell` from the menu
```
d. Install the package
```bash
pkg install qemu-guest-agent
```

And.. right as I ran the final command, I received an error saying I did not have internet. I pinged 8.8.8.8: Success. I pinged google.com: Fail.

I tried a few things (configuring the nameserver, reaching out directly to the OpenBSD ip address, etc), but for some reason (which I stil haven’t figured out) none of that worked. No worries, I had a different trick up my sleeve: reach out to the FreeBSD server from my PVE host, and get the ISO from the host to pfSense via a mount. Sweet, let’s give that a go.
1. Build the Installer ISO and stage the vm (on PVE host)
```bash
# Create a fresh clean staging workspace
mkdir -p /tmp/pfsense-offline && cd /tmp/pfsense-offline

# Grab the mirror catalog index file
wget https://pkg.freebsd.org/FreeBSD:14:amd64/latest/packagesite.pkg
tar -xf packagesite.pkg

# Pull out the live package path hash and download it
PKG_PATH=$(grep '"name":"qemu-guest-agent"' packagesite.yaml | sed -E 's/.*"path":"([^"]+)".*/\1/')
wget -O pfsense_gae.pkg "https://pkg.freebsd.org/FreeBSD:14:amd64/latest/${PKG_PATH}"

# Burn the local archive file into your ISO pool
genisoimage -o /var/lib/vz/template/iso/pfsense-offline.iso -V "AGENT_INSTALL" pfsense_gae.pkg
cd ~

# Provision your writable pfSense workspace and load the CD drive
qm clone 9201 99201 --full 1 --name tmpl-pfsense-patching
qm set 99201 --agent 1 --ide2 local:iso/pfsense-offline.iso,media=cdrom
qm start 99201
```
2. Override the interface wizard
Should VLANs be set up now? n
Enter the WAN interface name: vtnet0
Enter the LAN interface name: [Press Enter to skip]
Do you want to proceed? y
Press 8 to drop into the shell
3. Extract
```bash
# Mount the CD block volume
mkdir -p /mnt/cdrom
mount_cd9660 /dev/cd0 /mnt/cdrom

# Force extract the binary and configurations cleanly to the root directory
tar -xf /mnt/cdrom/pfsense_gae.pkg -C / --strip-components 1
umount /mnt/cdrom

# Mark the startup controller script executable
chmod +x /usr/local/etc/rc.d/qemu-guest-agent

# Configure the boot flags to point to the correct FreeBSD VirtIO port
echo 'qemu_guest_agent_enable="YES"' > /etc/rc.conf.local
echo 'qemu_guest_agent_flags="-d -v -p /dev/vtcon/org.qemu.guest_agent.0"' >> /etc/rc.conf.local

# Force-spin up the agent service bypassing local environment caching lag
service qemu-guest-agent onestart

# Exit and shut down
exit
```
4. Shutdown
Hit 6 to shut down the system
5. Verify usage
```bash
qm start <VMID>
qm agent <VMID> ping # this should return a blank line
qm stop <VMID>
qm template <VMID>
```

Now for OPNsense.
1. Build the installer iso and stage the vm
```bash
# Clean workspace environment
mkdir -p /tmp/opnsense-offline && cd /tmp/opnsense-offline

# Grab the live repository catalog database from the mirror index
wget https://pkg.freebsd.org/FreeBSD:14:amd64/latest/packagesite.pkg
tar -xf packagesite.pkg

# Pull out the exact matching filename hash and download it dynamically
PKG_PATH=$(grep '"name":"qemu-guest-agent"' packagesite.yaml | sed -E 's/.*"path":"([^"]+)".*/\1/')
wget "https://pkg.freebsd.org/FreeBSD:14:amd64/latest/${PKG_PATH}"

# Bake the package archive file into an ISO
genisoimage -o /var/lib/vz/template/iso/opnsense-offline.iso -V "AGENT_INSTALL" /tmp/opnsense-offline/*.pkg
cd ~

# Provision the writable OPNsense workspace and attach the CD drive
qm clone 9202 99202 --full 1 --name tmpl-opnsense-patching
qm set 99202 --agent 1 --ide2 local:iso/opnsense-offline.iso,media=cdrom

# Boot fresh so the BIOS maps the hardware block device node
qm start 99202
```
2. Pop into the opnsense shell
Log into the opnsense console and use your creds (default are root:opnsense)
3. Extract and target the serial character node
```bash
# Mount the virtual CD drive
mkdir -p /mnt/cdrom
mount_cd9660 /dev/cd0 /mnt/cdrom

# Force-extract the package blind to Python 3.11 dependency metadata restrictions
tar -xf /mnt/cdrom/qemu-guest-agent-*.pkg -C / --strip-components 1
umount /mnt/cdrom

# Make the service script executable
chmod +x /usr/local/etc/rc.d/qemu-guest-agent

# Set up the startup configurations pointing to the /dev/vtcon/ serial port
echo 'qemu_guest_agent_enable="YES"' > /etc/rc.conf.local
echo 'qemu_guest_agent_flags="-d -v -p /dev/vtcon/org.qemu.guest_agent.0"' >> /etc/rc.conf.local

# Kick the background daemon engine
service qemu-guest-agent start

# Exit the shell
exit
```
4. Verify and seal the deal
```bash
qm start <VMID>
qm agent <VMID> ping
qm stop <VMID>
qm template <VMID>
```

### Standard ISO vs Cloud-Init ISO Explained

This is a bit of a tangent, but I think it is really interesting--so let me break what makes the cloudinit iso so special.

Before that, let’s understand what a standard ISO (or ISO image or ISO file) is. Simply put, it is a byte-for-byte copy of an optical disk (eg. a CD, DVD, etc). It is often used to boot into an OS’s installer. The architecture looks something like this
```text
  /
  ┼─ .disk/   # CD-ROM metadata and architecture info    
  ┼─ boot/
  │ ┼─ grub/   # bootloader configurations
  │ └─ efi.img   # FAT-formatted EFI system partition image
  ┼─ install/
  │ ┼─ vmlinuz   # compressed Linux kernel
  │ └─ initrd.gz  # initial RAM filesystem containing drivers
  ┼─ pool/main/z  # massive repo of compressed .deb/.rpm archives
```

Of note here, there is a bootloader and kernel (among other things). A cloudinit ISO is completely different. There is no bootloader, no kernel, nor most of the stuff in a standard ISO. Instead, the ISO looks a little bit like this
```text
  /
  ┼─ meta-data   # key-value pairs (instance-id, hostname)
  ┼─ user-data # cloud-config yaml or shell scripts
  ┼─ network-config  # network configuration
```

I read about the stuff I just synthesized for you, but I wanted to take a closer look. Luckily enough, to do that is quite simple.
```bash

```

So, clearly, the two ISOs serve completely different purposes. As you may or may not be able to tell, the cloudinit ISO’s sole purpose is to serve as an instruction manual for what the main iso should do. It acts as a guide on install, automating the install process alongside the earlier downloaded cloud iso. It is very similar to the relationship between a windows11.iso and autounattend.iso--in this case, the autounattend.iso guides the windows 11 install autonomously

## Using the Templates

As I began working on this project, I was planning on implementing (and had done so to an extent in my first iteration) the network configuration (including, namely, provisioning the VMs) with only qm. I mean.. qm is insanely powerful, so why not do it? Well, I ultimately did it because it is not as convenient as using Python with PVE’s APIs and proxmoxer. Plus, I had not yet implemented vlanning for teams (which I knew I would have to do) and it would be just a few more lines of code.

### Interacting with PVE via Python

We have two main options here: we can either use PVE's REST API (via raw requests) or [proxmoxer](https://proxmoxer.github.io/docs/2.0/), a wrapper around said API.

Connecting to PVE is quite simple:
```python
from proxmoxer import ProxmoxAPI
from django.conf import settings

cfg = settings.PROXMOX
prox = ProxmoxAPI(
    cfg["host"],
    user=cfg["user"],
    token_name=cfg["token_name"],
    token_value=cfg["token_value"],
    verify_ssl=cfg["verify_ssl"],
)
```

> There are two ways in which we can authenticate to PVE: `username:password` and API tokens. For obvious reasons, tokens are much better. You can create one at Datacenter --> Permissions --> API Tokens --> Add. At a minimum, you'll want to configure it with `VM.Clone`, `VM.Config`, and `VM.PowerMgmt`.

### Cloning a Template

With templates sitting at VMIDs 9000–9027, cloning one for a team is a few lines.
```python
task_id = prox.nodes(node).qemu(template_vmid).clone.post(
    newid=new_vmid,
    name=vm_name,
    full=1,
    target=node,
)
```

Of note, the clone is **asynchronous**. `clone.post()` returns a task ID immediately, so you'll have to poll until it's done before you can configure or start the VM.
```python
import time

def wait_for_task(prox, node, task_id, timeout=300):
    deadline = time.time() + timeout
    while time.time() < deadline:
        status = prox.nodes(node).tasks(task_id).status.get()
        if status["status"] == "stopped":
            if status.get("exitstatus") == "OK":
                return
            raise RuntimeError(f"Task failed: {status.get('exitstatus')}")
        time.sleep(3)
    raise TimeoutError(f"Task {task_id} timed out")
```

### Utilizing cloud-init

After cloning, we can use cloud-init to configure the VM.
```python
prox.nodes(node).qemu(new_vmid).config.post(
    ciuser=f"team{team_number}",
    cipassword=team_password,
    ipconfig0="ip=dhcp",
    net0=f"virtio,bridge={bridge}",
)
prox.nodes(node).qemu(new_vmid).status.start.post()
```

### VMID Numbering Scheme

Even though this bit is abstracted away from the user, it is still a nice feature considering there is certainly possibility for hopping in PVE to figure stuff out. As such, I decided on the following schema:
- Templates: 9000–9099 (created by `create_templates.sh`)  
- Competition VMs: `5 + TT + CC`, where TT is the two-digit team number and CC is a per-team counter  
  - Team 1: 50100, 50101, 50102, ...  
  - Team 2: 50200, 50201, 50202, ...

In the future, I may move to terraform as it is declarative (you tell it what you want and it does it--and it can be used on a ton of platforms, not just ProxMox. However, after a couple of days of researching terraform, I’ve come to realize it isn’t something I want to learn at the moment (I want to stay focused on learning the current technologies), although I certainly see room for it in the future.

## Questions or Advice?

Do you have any questions? Did I say something wrong? Do you have any advice? Please ask, critique, and teach me at amcantor@umd.edu or `@_z4n1` on Discord!

