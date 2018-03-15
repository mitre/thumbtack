#!/usr/bin/env bash
sudo apt update

# install thumbtack forensics library dependencies
sudo apt install -y afflib-tools \
                    archivemount \
                    avfs \
                    cryptsetup \
                    disktype \
                    exfat-fuse \
                    exfat-utils \
                    ewf-tools \
                    libbde-utils \
                    libguestfs-tools \
                    libvshadow-utils \
                    lvm2 \
                    mdadm \
                    mtd-utils \
                    ocfs2-tools \
                    open-vm-tools \
                    qemu-utils \
                    sleuthkit \
                    squashfs-tools \
                    vmfs-tools \
                    xfsprogs \
                    xmount \
                    zlib1g-dev

# install other useful tools
sudo apt install -y python3-pip \
                    p7zip-full \
                    tree \
                    vim-nox \
                    virtualenvwrapper \
                    unzip \
                    zip

cd /vagrant
# install the thumbtack python library in development mode
sudo pip3 install -e .[dev]
