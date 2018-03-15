.. _quickstart:

Quick Start
===========

This document presents a quick walkthrough on how to use Thumbtack.
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

Thumbtack is a `Flask`_ powered web application.
We'll use the built in `Flask server`_ in this tutorial.

Put the ``wsgi.py`` file from the top level of the repo in your working directory.
Then, as a user with admin privileges, run the following commands.
The ``IMAGE_DIR`` environment variable refers to the directory you created in the previous step.

.. code-block:: bash

    wget https://raw.githubusercontent.com/mitre/thumbtack/master/wsgi.py
    sudo -E IMAGE_DIR=/path/to/disk_images flask run

The Thumbtack server is now listening on port 5000, and can be accessed from a web browser at http://127.0.0.1:5000

Development Environment
-----------------------

If you are planning to contribute to the development of Thumbtack, you should clone the repository from GitHub rather than installing a released version from PyPI.
As above, we recommend using a virtualenv.

.. code-block:: bash

    git clone https://github.com/mitre/thumbtack.git
    cd thumbtack
    # Install any required OS libraries for mounting images. See the imagemounter documentation.
    pip install -r requirements.txt
    sudo -E FLASK_ENV=development flask run

    # in order to be able to access the thumbtack server from another machine - potentially DANGEROUS!
    sudo -E FLASK_ENV=development flask run -h 0.0.0.0

.. _multiple ways: https://docs.python-guide.org/dev/virtualenvs
.. _virtualenvwrapper: https://virtualenvwrapper.readthedocs.io/en/latest/index.html
.. _Pipenv: https://pipenv.readthedocs.io/en/latest
.. _DFTT: http://dftt.sourceforge.net
.. _Digital Corpora: https://digitalcorpora.org
.. _Flask: http://flask.pocoo.org
.. _Flask server: http://flask.pocoo.org/docs/1.0/server
