.. image:: https://travis-ci.org/mitre/thumbtack.svg?branch=master
    :target: https://travis-ci.org/mitre/thumbtack

thumbtack
=========

Thumbtack is a web front-end providing a REST-ful API to mount and unmount
forensic disk images, built on top of the |imagemounter|_ library.

Documentation is available in the ``docs/`` directory or online at
https://thumbtack.readthedocs.io/en/latest.

Quick Start
-----------

.. code-block:: bash

    $ pip install thumbtack
    $ cd path/to/disk/image/files
    $ thumbtack
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

    $ thumbtack --help
    Usage: thumbtack [OPTIONS]

    Options:
      -d, --debug           Run the Thumbtack server in debug mode
      -h, --host TEXT       Host to run Thumbtack server on  [default: 127.0.0.1]
      -p, --port TEXT       Port to run Thumbtack server on  [default: 8208]
      -i, --image-dir TEXT  Directory of disk images for Thumbtack server to
                            monitor  [default: $CWD]
      --db TEXT             SQLite database to store mount state  [default:
                            database.db]
      --help                Show this message and exit.

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
