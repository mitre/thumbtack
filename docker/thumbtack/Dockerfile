# This docker image is used for thumbtack
FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

EXPOSE 8208

RUN apt-get update --fix-missing
RUN apt-get -y install gosu
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Install imagemounter dependencies
RUN apt install -y afflib-tools archivemount avfs cryptsetup disktype ewf-tools exfat-fuse exfat-utils fuse3 libbde-utils libewf-dev libfuse-dev libguestfs-tools libmagic1 libvshadow-utils lvm2 mdadm mtd-tools mtd-utils ocfs2-tools open-vm-tools qemu-utils sleuthkit squashfs-tools vmfs-tools vmfs6-tools xfsprogs xmount zlib1g-dev libfuse3-dev
RUN apt install -y git autoconf automake autopoint libtool pkg-config

# Install thumbtack
RUN apt install -y python3 python3-pip
RUN pip install thumbtack==0.5.5

#### Install libewf
WORKDIR "/src/"
RUN apt install -y wget
RUN wget https://github.com/libyal/libewf/releases/download/20240506/libewf-experimental-20240506.tar.gz
RUN tar -xf libewf-experimental-20240506.tar.gz
WORKDIR "/src/libewf-20240506/"
RUN ./configure --enable-python3 --with-libfuse --enable-static-executables && make && make install

#### Install bde
WORKDIR "/src/"
RUN wget https://github.com/libyal/libbde/releases/download/20240502/libbde-alpha-20240502.tar.gz
RUN tar -xf libbde-alpha-20240502.tar.gz
WORKDIR "/src/libbde-20240502"
RUN ./configure --enable-static-executables=yes  && make && make install



WORKDIR "/"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
