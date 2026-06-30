#!/bin/bash

cd /var/lib/vz/template/iso # cd into where the template isos are stored

create_lin_templates() {
    # download all of the cloud images
    wget https://cdimage.debian.org/cdimage/openstack/archive/8.11.0/debian-8.11.0-openstack-amd64.qcow2 -O debian-8-genericcloud-amd64.qcow2
    wget https://cdimage.debian.org/cdimage/cloud/OpenStack/archive/9.9.0/debian-9.9.0-openstack-amd64.qcow2 -O debian-9-genericcloud-amd64.qcow2
    wget https://cdimage.debian.org/images/cloud/OpenStack/archive/10.13.0/debian-10.13.0-openstack-amd64.qcow2 -O debian-10-genericcloud-amd64.qcow2
    wget https://cloud.debian.org/images/cloud/bullseye/latest/debian-11-genericcloud-amd64.qcow2 -O debian-11-genericcloud-amd64.qcow2
    wget https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-genericcloud-amd64.qcow2 -O debian-12-genericcloud-amd64.qcow2

    wget https://cloud-images.ubuntu.com/releases/trusty/release/ubuntu-14.04-server-cloudimg-amd64-disk1.img -O ubuntu-1404-cloudimg-amd64.img
    wget https://cloud-images.ubuntu.com/releases/xenial/release/ubuntu-16.04-server-cloudimg-amd64-disk1.img -O ubuntu-1604-cloudimg-amd64.img
    wget https://cloud-images.ubuntu.com/releases/bionic/release/ubuntu-18.04-server-cloudimg-amd64.img -O ubuntu-1804-cloudimg-amd64.img
    wget https://cloud-images.ubuntu.com/releases/jammy/release/ubuntu-22.04-server-cloudimg-amd64.img -O ubuntu-2204-cloudimg-amd64.img
    wget https://cloud-images.ubuntu.com/releases/noble/release/ubuntu-24.04-server-cloudimg-amd64.img -O ubuntu-2404-cloudimg-amd64.img

    wget https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2 -O centos7-genericcloud-amd64.qcow2
    wget https://cloud.centos.org/centos/6/images/CentOS-6-x86_64-GenericCloud.qcow2 -O centos6-genericcloud-amd64.qcow2

    wget https://dl.rockylinux.org/pub/rocky/9/images/x86_64/Rocky-9-GenericCloud.latest.x86_64.qcow2 -O rocky9-genericcloud-amd64.qcow2
    wget https://repo.almalinux.org/almalinux/8/cloud/x86_64/images/AlmaLinux-8-GenericCloud-latest.x86_64.qcow2 -O almalinux8-genericcloud-amd64.qcow2

    wget https://download.opensuse.org/distribution/leap/15.5/appliances/openSUSE-Leap-15.5-Minimal-VM.x86_64-Cloud.qcow2 -O opensuse-15-cloud.qcow2
    wget https://archives.fedoraproject.org/pub/archive/fedora/linux/releases/32/Cloud/x86_64/images/Fedora-Cloud-Base-32-1.6.x86_64.qcow2 -O fedora32-cloudbase-amd64.qcow2
    wget https://geo.mirror.pkgbuild.com/images/latest/Arch-Linux-x86_64-cloudimg.qcow2 -O arch-cloudimg-amd64.qcow2
    wget https://dl-cdn.alpinelinux.org/alpine/v3.22/releases/cloud/generic_alpine-3.22.2-x86_64-bios-cloudinit-r0.qcow2 -O alpine-cloudimg-amd64.qcow2

    # make the templates
    declare -A templates

    templates[9000] = "debian-8-genericcloud-amd64.qcow2"
    templates[9001] = "debian-9-genericcloud-amd64.qcow2"
    templates[9002] = "debian-10-genericcloud-amd64.qcow2"
    templates[9003] = "debian-11-genericcloud-amd64.qcow2"
    templates[9004] = "debian-12-genericcloud-amd64.qcow2"

    templates[9010] = "ubuntu-1404-cloudimg-amd64.img"
    templates[9011] = "ubuntu-1604-cloudimg-amd64.img"
    templates[9012] = "ubuntu-1804-cloudimg-amd64.img"
    templates[9013] = "ubuntu-2204-cloudimg-amd64.img"
    templates[9014] = "ubuntu-2404-cloudimg-amd64.img"

    templates[9020] = "centos6-genericcloud-amd64.qcow2"
    templates[9021] = "centos7-genericcloud-amd64.qcow2"
    templates[9022] = "rocky9-genericcloud-amd64.qcow2"
    templates[9023] = "almalinux8-genericcloud-amd64.qcow2"
    templates[9024] = "opensuse-15-cloud.qcow2"
    templates[9025] = "fedora32-cloudbase-amd64.qcow2"
    templates[9026] = "arch-cloudimg-amd64.qcow2"
    templates[9027] = "alpine-cloudimg-amd64.qcow2"

    for id in "${!templates[@]}"; do
    downloaded_file="${templates[$id]}"
    if [ -f "$downloaded_file" ]; then
        echo "Creating template for $downloaded_file with ID $id"
        qm create "$id" --name "${downloaded_file%.*}" --memory 2048 --net0 virtio,bridge=vmbr0 --ide2 local:cloudinit --boot c --scsihw virtio-scsi-pci --scsi0 local-lvm:0,import-from="$downloaded_file"
        qm set "$id" --serial0 socket --vga serial0
        qm set "$id" --ciuser clouduser --cipassword cloudpassword
        qm set "$id" --sshkey ~/.ssh/id_rsa.pub
        qm template "$id"
        echo "Template for $downloaded_file with ID $id created successfully"
    else
        echo "File $downloaded_file not found, skipping template creation for ID $id"
    fi
    done
}

create_win_templates() {
    # download all of the windows images
    echo "For Windows 11, go to https://www.microsoft.com/en-us/evalcenter/evaluate-windows-11-enterprise > Download the ISO - Windows 11 Enterprise LTSC > Download now > ISO - Enterprise LTSC Download > 64-bit edition > Save to /var/lib/vz/template/iso/Win11_22H2_English_x64.iso"
    echo "For Windows Server 2016, go to https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2016 > Download the ISO > Download now > ISO - Windows Server 2016 > 64-bit edition > Save to /var/lib/vz/template/iso/WinServer2016_English_x64.iso"
    echo "For Windows Server 2019, go to https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2019 > Download the ISO > Download now > ISO - Windows Server 2019 > 64-bit edition > Save to /var/lib/vz/template/iso/WinServer2019_English_x64.iso"
    echo "For Windows Server 2022, go to https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2022 > Download the ISO > Download now > ISO - Windows Server 2022 > 64-bit edition > Save to /var/lib/vz/template/iso/WinServer2022_English_x64.iso"
    echo "For Windows Server 2025, go to https://www.microsoft.com/en-us/evalcenter/evaluate-windows-server-2025 > Download the ISO > Download now > ISO - Windows Server 2025 > 64-bit edition > Save to /var/lib/vz/template/iso/WinServer2025_English_x64.iso"
    # make the templates
    declare -A templates

    templates[9100] = "Win10_22H2_English_x64.iso"
    templates[9101] = "Win11_22H2_English_x64.iso"

    for id in "${!templates[@]}"; do
        downloaded_file="${templates[$id]}"
        if [ -f "$downloaded_file" ]; then
            echo "Creating template for $downloaded_file with ID $id"
            qm create "$id" --name "${downloaded_file%.*}" --memory 4096 --net0 virtio,bridge=vmbr0 --ide2 local:cloudinit --boot c --scsihw virtio-scsi-pci --scsi0 local-lvm:0,import-from="$downloaded_file"
            qm set "$id" --serial0 socket --vga serial0
            qm set "$id" --ciuser clouduser --cipassword cloudpassword
            qm set "$id" --sshkey ~/.ssh/id_rsa.pub
            qm template "$id"
            echo "Template for $downloaded_file with ID $id created successfully"
        else
            echo "File $downloaded_file not found, skipping template creation for ID $id"
        fi
    done
}