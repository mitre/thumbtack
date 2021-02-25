.. _tutorial:

Tutorial
========

This document presents a short walkthrough on how to use Thumbtack.
Please refer to the links throughout the document for further information.

If you only want to test Thumbtack out, using the Flask development server will suffice.

Installation
------------

In order to install Thumbtack, you should use a virtual environment, which will allow you to keep Thumbtack dependencies separate from system Python packages.
There are `multiple ways`_ to use virtual environments these days, but we recommend the use of `virtualenvwrapper`_.
In the future we may update this to use `Pipenv`_ instead.

Install ``virtualenvwrapper`` on Ubuntu:

.. code-block:: bash

    sudo apt install virtualenvwrapper
    mkvirtualenv -p /usr/bin/python3 thumbtack

Once you have a virtual environment created and activated, use ``pip`` to install the Thumbtack server.

.. code-block:: bash

    pip3 install thumbtack

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
      -d, --debug           Run the Thumbtack server in debug mode
      -h, --host TEXT       Host to run Thumbtack server on  [default: 127.0.0.1]
      -p, --port TEXT       Port to run Thumbtack server on  [default: 8208]
      -m, --mount-dir TEXT  Directory to mount disk images  [Default:
                            /mnt/thumbtack]

      -i, --image-dir TEXT  Directory of disk images for Thumbtack server to
                            monitor  [Default: $CWD]

      --db TEXT             SQLite database to store mount state
      -b, --base-url TEXT   Base URL where Thumbtack is hosted on the server
                            [default: /]

      --help                Show this message and exit.

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

Pseudo-Production Environment
-----------------------------

As mentioned on the homepage of the documentation, Thumbtack should not run in a production setting for security reasons.
However, if you would like to get Thumbtack to work with a webserver like Nginx or Apache, a `wsgi.py` file is provided at the top level of the repo.
Once again, for more information on deploying Flask applications, please refer to Flask's `deployment documentation`_.


.. _multiple ways: https://docs.python-guide.org/dev/virtualenvs
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/index.html
.. _Pipenv: https://pipenv.readthedocs.io/en/latest
.. _DFTT: http://dftt.sourceforge.net
.. _Digital Corpora: https://digitalcorpora.org
.. _Flask: http://flask.pocoo.org
.. _Flask server: http://flask.pocoo.org/docs/1.0/server
.. _deployment documentation: http://flask.pocoo.org/docs/1.0/deploying
