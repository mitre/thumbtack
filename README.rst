
thumbtack
=========

Thumbtack is a web front-end providing a REST-ful API to mount and unmount
forensic disk images, built on top of the |imagemounter|_ library.

Documentation is available in the ``docs/`` directory or online at
https://thumbtack.readthedocs.io/en/latest.

Quick Start
-----------

.. code-block:: bash

    $ sudo pip install thumbtack
    $ sudo imount --check # List install status of tools used by imagemounter
    The following commands are used by imagemounter internally. Without most commands, imagemounter works perfectly fine, but may lack some detection or mounting capabilities.
    -- Mounting base disk images (at least one required, first three recommended) --
    MISSING   xmount              needed for several types of disk images, part of the xmount package
    MISSING   ewfmount            needed for EWF images (partially covered by xmount), part of the ewf-tools package
    MISSING   affuse              needed for AFF images (partially covered by xmount), part of the afflib-tools package
    MISSING   vmware-mount        needed for VMWare disks
    MISSING   mountavfs           needed for compressed disk images, part of the avfs package
    MISSING   qemu-nbd            needed for Qcow2 images, part of the qemu-utils package
    ...
    

Install additional tools needed to mount your images. More information can be found in the imagemounter installation docs https://imagemounter.readthedocs.io/en/latest/installation.html.


.. code-block:: bash

    # Install tools
    $ sudo apt-get install xmount ewf-tools afflib-tools sleuthkit
    $ cd path/to/disk/image/files
    $ sudo thumbtack
      * Serving Flask app "thumbtack" (lazy loading)
      * Environment: production
        WARNING: This is a development server. Do not use it in a production deployment.
        Use a production WSGI server instead.
      * Debug mode: off
      * Running on http://127.0.0.1:8208/ (Press CTRL+C to quit)


Then go to http://127.0.0.1:8208 and start mounting and unmounting images!

Find a full tutorial in ``docs/tutorial.rst``.

Quick Reference
---------------

.. code-block:: bash

    $ sudo thumbtack --help
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

LICENSE
-------

Thumbtack is licensed under the `Apache License, Version 2.0
<https://www.apache.org/licenses/LICENSE-2.0.html>`_. See the `LICENSE` file for
more information.

RELEASE STATEMENT
-----------------
Approved for Public Release; Distribution Unlimited. Public Release Case Number 19-0358.


.. |imagemounter| replace:: ``imagemounter``
.. _imagemounter: https://imagemounter.readthedocs.io/en/latest/
