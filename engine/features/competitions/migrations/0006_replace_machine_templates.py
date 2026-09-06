from django.db import migrations

# Full template list from blog post "Templatization Everywhere"
# VMID scheme: 9000-9099 (templates), matching create_templates.sh convention
# (name, os_family, role, proxmox_vmid)
MACHINE_TEMPLATES = [
    # Linux — Debian
    ("Debian 8",            "linux",   "Generic",   9001),
    ("Debian 9",            "linux",   "Generic",   9002),
    ("Debian 10",           "linux",   "Generic",   9003),
    ("Debian 11",           "linux",   "Generic",   9004),
    ("Debian 12",           "linux",   "Generic",   9005),
    # Linux — Ubuntu
    ("Ubuntu 14.04",        "linux",   "Generic",   9010),
    ("Ubuntu 16.04",        "linux",   "Generic",   9011),
    ("Ubuntu 18.04",        "linux",   "Generic",   9012),
    ("Ubuntu 22.04",        "linux",   "Generic",   9013),
    ("Ubuntu 24.04",        "linux",   "Generic",   9014),
    # Linux — other distros
    ("Rocky Linux 9",       "linux",   "Generic",   9020),
    ("openSUSE Leap 15.5",  "linux",   "Generic",   9021),
    ("CentOS 6",            "linux",   "Generic",   9022),
    ("CentOS 7",            "linux",   "Generic",   9023),
    ("Fedora 31",           "linux",   "Generic",   9024),
    ("Arch Linux",          "linux",   "Generic",   9025),
    ("Alpine Linux",        "linux",   "Generic",   9026),
    ("AlmaLinux",           "linux",   "Generic",   9027),
    # Windows
    ("Windows Server 2016", "windows", "Generic",   9040),
    ("Windows Server 2019", "windows", "Generic",   9041),
    ("Windows Server 2022", "windows", "Generic",   9042),
    ("Windows Server 2025", "windows", "Generic",   9043),
    ("Windows 10",          "windows", "Generic",   9044),
    ("Windows 11",          "windows", "Generic",   9045),
    # Firewalls
    ("OPNsense",            "network", "Firewall",  9050),
    ("pfSense",             "network", "Firewall",  9051),
]

OLD_TEMPLATES = [
    "Windows Server 2019 - Domain Controller",
    "Windows Server 2019 - IIS Web Server",
    "Windows 10 Workstation",
    "Ubuntu 22.04 - Web Server",
    "Ubuntu 22.04 - Mail Server",
    "Rocky Linux 9 - Database Server",
    "pfSense Firewall",
    "Kali Linux - Jump Box",
]


def replace_templates(apps, schema_editor):
    MachineTemplate = apps.get_model("competitions", "MachineTemplate")
    MachineTemplate.objects.filter(name__in=OLD_TEMPLATES).delete()
    for name, os_family, role, vmid in MACHINE_TEMPLATES:
        MachineTemplate.objects.get_or_create(
            name=name,
            defaults={"os_family": os_family, "role": role, "proxmox_vmid": vmid},
        )


def reverse_templates(apps, schema_editor):
    MachineTemplate = apps.get_model("competitions", "MachineTemplate")
    MachineTemplate.objects.filter(name__in=[t[0] for t in MACHINE_TEMPLATES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('competitions', '0005_provisionedmachine'),
    ]

    operations = [
        migrations.RunPython(replace_templates, reverse_templates),
    ]
