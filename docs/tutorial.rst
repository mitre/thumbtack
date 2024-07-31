.. _tutorial:

Tutorial
========

This document presents a short walkthrough on how to use Thumbtack.
Please refer to the links throughout the document for further information.


Installation
------------

In order to install Thumbtack, you should use a virtual environment, which will allow you to keep Thumbtack dependencies separate from system Python packages.

.. note::

    Due to restrictions of several disk-mounting utilities, Thumbtack should be installed and run as the root user.

Create and activate the virtual environment:

.. code-block:: bash

    sudo apt-get install python3-venv
    python -m venv ./thumbtack

Once you have a virtual environment created and activated, use ``pip`` to install the Thumbtack server.

.. code-block:: bash

    source ./thumbtack/bin/activate
    pip install thumbtack

Install Imagemounter Dependencies
---------------------------------

Thumbtack uses the ``imagemounter`` library, which has a set of dependencies required to mount different types of disk images.
Follow the `imagemounter install instructions`_ to install required dependencies. You can also run ``imount --check`` to get a list of
dependencies as well as install status.


.. code-block:: bash

    $ imount --check
    The following commands are used by imagemounter internally. Without most commands, imagemounter works perfectly fine, but may lack some detection or mounting capabilities.
    -- Mounting base disk images (at least one required, first three recommended) --
    MISSING   xmount              needed for several types of disk images, part of the xmount package
    MISSING   ewfmount            needed for EWF images (partially covered by xmount), part of the ewf-tools package
    MISSING   affuse              needed for AFF images (partially covered by xmount), part of the afflib-tools package
    MISSING   vmware-mount        needed for VMWare disks
    MISSING   mountavfs           needed for compressed disk images, part of the avfs package
    MISSING   qemu-nbd            needed for Qcow2 images, part of the qemu-utils package
    -- Detecting volumes and volume types (at least one required) --
    MISSING   mmls                part of the sleuthkit package
    MISSING   pytsk3              install using pip
    INSTALLED parted
    -- Detecting volume types (all recommended, first two highly recommended) --
    MISSING   fsstat              part of the sleuthkit package
    INSTALLED file
    INSTALLED blkid
    MISSING   python-magic        install using pip
    MISSING   disktype            part of the disktype package
    -- Mounting volumes (install when needed) --
    INSTALLED xfs
    INSTALLED ntfs
    MISSING   lvm                 needed for LVM volumes, part of the lvm2 package
    MISSING   vmfs-fuse           needed for VMFS volumes, part of the vmfs-tools package
    INSTALLED jffs2
    INSTALLED squashfs
    MISSING   mdadm               needed for RAID volumes, part of the mdadm package
    MISSING   cryptsetup          needed for LUKS containers, part of the cryptsetup package
    MISSING   bdemount            needed for Bitlocker Drive Encryption volumes, part of the libbde-utils package
    MISSING   vshadowmount        needed for NTFS volume shadow copies, part of the libvshadow-utils package
    MISSING   photorec            needed for carving free space, part of the testdisk package


Create Directory of Disk Images
-------------------------------

You will need to have a directory of disk images that Thumbtack will be configured to monitor.
Thumbtack will automatically assume that every file in this directory is a disk image, so be advised that other filetypes will automatically fail to mount.
You may use the following script from the Thumbtack repository to download some test images from `DFTT`_ or `Digital Corpora`_.
The script will give estimated download size and ask permission before downloading.

.. code-block:: bash

    mkdir disk_images
    cd disk_images
    wget https://raw.githubusercontent.com/mitre/thumbtack/master/tests/download-test-images.py
    python download_test_images.py

Run the Server
--------------

Here's the easy part!
Just make sure to be in the directory where your disk images are as mentioned above in the Create Directory of Disk Images section.

.. code-block:: bash

    thumbtack

The Thumbtack server is now listening on port 8208, and can be accessed from a web browser at http://127.0.0.1:8208

There are a few options that the `thumbtack` command can take, allowing you to change the host, port, image directory, and sqlite database file.
See them below.

.. code-block:: bash

    $ thumbtack --help
    Usage: thumbtack [OPTIONS]

    Options:
      -d, --debug                   Run the Thumbtack server in debug mode
      -h, --host TEXT               Host to run Thumbtack server on  [default: 127.0.0.1]
      -p, --port TEXT               Port to run Thumbtack server on  [default: 8208]
      -m, --mount-dir TEXT          Directory to mount disk images  [Default: /mnt/thumbtack]
      -i, --image-dir TEXT          Directory of disk images for Thumbtack server to monitor  [Default: $CWD]
      --db TEXT                     SQLite database to store mount state
      -b, --base-url TEXT           Base URL where Thumbtack is hosted on the server  [default: /]
      --path-contains TEXT          Only select files containing specified string in the path
      -s, --skip-subdirectory TEXT  Subdirectory to ignore when monitoring files
      -r, --remove-directories      Unmount all mountpoints and remove all empty directories in the thumbtack mount directory
      --help                        Show this message and exit.

Development Environment
-----------------------

If you are planning to contribute to the development of Thumbtack, you should clone the repository from GitHub rather than installing a released version from PyPI.
Vagrant is recommended and a fully functioning `Vagrantfile` is provided at the top level of the repo.
It will install an Ubuntu 16.04 VirtualBox VM locally with all libraries required as well as Thumbtack.

.. code-block:: bash

    # Install Vagrant
    # Install VirtualBox
    git clone https://github.com/mitre/thumbtack.git
    cd thumbtack
    vagrant up
    vagrant ssh

    # inside Vagrant machine
    cd /vagrant/tests
    python download_test_images.py
    cd test_images
    thumbtack -h 0.0.0.0

The Vagrant VM will be running the Thumbtack server on port 8208, and is set up to automatically forward the port to your localhost.
You should be able to access the web interface via http://127.0.0.1:8208 now.

Thumbtack in Docker
-------------------

Thumbtack can be run in a docker container. A template docker-compose file is included in the thumbtack repository.

.. code-block:: bash

    apt-get install docker.io docker-compose
    git clone https://github.com/mitre/thumbtack.git

Copy and fill out the ``docker-compose.yml`` file. Replace all instances of ``image_dir`` with
the absolute path the the image directory. Replace all instances of ``mount_dir`` with the absolute
path to the directory where images should be mounted. You may add additional options to the command
as needed.

.. code-block:: bash

    cd docker
    cp docker-compose.yml.template docker-compose.yml

After filling out the docker-compose template, start the docker container.

.. code-block:: bash

    docker-compose up

Navigate to http://127.0.0.1:8208 to use thumbtack.

.. note::

    To enable mounting lvm volumes within docker, you must install the ``lvm2`` package on the host system.

    .. code-block:: bash

        sudo apt-get install lvm2

Pseudo-Production Environment
-----------------------------

If you would like to get Thumbtack to work with a webserver like Nginx or Apache, a `wsgi.py` file is provided at the top level of the repo.
Once again, for more information on deploying Flask applications, please refer to Flask's `deployment documentation`_.

Including FUSE for EWF images
-----------------------------

In order to mount EWF images, the libewf package needs to be installed and configured to support FUSE. The following steps can be used to install the package.

.. code-block:: bash

    sudo apt install autoconf automake autopoint libtool pkg-config libfuse-dev zlib1g-dev
    wget https://github.com/libyal/libewf/releases/download/20201230/libewf-experimental-20201230.tar.gz
    tar -xavf libewf-experimental-20201230.tar.gz
    cd libewf-20201230/
    ./configure --enable-python3 --with-libfuse
    make
    sudo make install

.. _multiple ways: https://docs.python-guide.org/dev/virtualenvs
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/index.html
.. _Pipenv: https://pipenv.readthedocs.io/en/latest
.. _DFTT: http://dftt.sourceforge.net
.. _Digital Corpora: https://digitalcorpora.org
.. _Flask: http://flask.pocoo.org
.. _Flask server: http://flask.pocoo.org/docs/1.0/server
.. _deployment documentation: http://flask.pocoo.org/docs/1.0/deploying
.. _imagemounter install instructions: https://imagemounter.readthedocs.io/en/latest/installation.html
