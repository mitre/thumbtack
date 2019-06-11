Thumbtack
=========

Thumbtack is a `Flask`_ powered web front-end providing a REST-ful API to mount and unmount forensic disk images, built on top of the |imagemounter|_ library.
It supports the mounting of many `disk image file types`_, depending on which supporting libraries are installed.

.. note::

    Though imagemounter will work on any Unix- or Linux-based OS that has support for the underlying mounting utilities, only the Ubuntu Linux distribution has been used to test Thumbtack.

.. warning::

    DO NOT USE THIS TOOL IN A PRODUCTION SETTING!
    Due to the user restrictions of most disk-mounting utilities, you will have more success with Thumbtack when it is run as root.
    For more information on deploying Flask applications, please refer to Flask's `deployment documentation`_.

.. toctree::
    :maxdepth: 2
    :caption: Contents

    tutorial
    api_guide
    thumbtack_client
    web-interface
    about
    releasenotes/index.rst
    source/modules.rst


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. _Flask: http://flask.pocoo.org
.. |imagemounter| replace:: ``imagemounter``
.. _imagemounter: https://imagemounter.readthedocs.io/en/latest/
.. _disk image file types: https://imagemounter.readthedocs.io/en/latest/specifics.html
.. _deployment documentation: http://flask.pocoo.org/docs/1.0/deploying
