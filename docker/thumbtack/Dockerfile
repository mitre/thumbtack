# This docker image is used for thumbtack
FROM ubuntu:20.04

ARG DEBIAN_FRONTEND=noninteractive

EXPOSE 8208

RUN apt-get update --fix-missing
RUN apt-get -y install gosu
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

# Install imagemounter dependencies
RUN apt install -y afflib-tools archivemount avfs cryptsetup disktype ewf-tools exfat-fuse exfat-utils fuse libbde-utils libewf-dev libfuse-dev libguestfs-tools libmagic1 libvshadow-utils lvm2 mdadm mtd-tools mtd-utils ocfs2-tools open-vm-tools qemu-utils sleuthkit squashfs-tools vmfs-tools vmfs6-tools xfsprogs xmount zlib1g-dev

# Install thumbtack
RUN apt install -y python3 python3-pip git
RUN pip install thumbtack

WORKDIR "tmp/"
RUN apt install -y wget
RUN wget https://github.com/libyal/libewf/releases/download/20201230/libewf-experimental-20201230.tar.gz
RUN tar -xf libewf-experimental-20201230.tar.gz
WORKDIR "/tmp/libewf-20201230/"
RUN ./configure --enable-python3 --with-libfuse && make && make install
RUN cp /usr/local/lib/libewf* /usr/lib/
RUN rm -rf /tmp/libewf-experimental-20201230*


WORKDIR "/"

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
