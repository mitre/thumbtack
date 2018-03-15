.. _api_guide:

API Guide
=========

API Endpoints
-------------
You can access information regarding images Thumbtack knows about through its API endpoints.
Alternately, you can use the :ref:`thumbtack_client`

/mount/
*******
Accessing this endpoint allows you to get information on all of the disk images that are currently mounted.

/mount/<path:image_path>
************************
Gets you information about a specific disk image that is currently mounted. If that disk image is not currently
mounted, it returns a ``404`` error with a message stating that the requested disk image is not mounted.

/supported/
********************
This endpoint returns a JSON object containing information about which supporting libraries are installed and
which are not.
