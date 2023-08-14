.. _api_guide:

API Guide
=========

API Endpoints
-------------
You can access information regarding images Thumbtack knows about through its API endpoints.
Alternately, you can use the `thumbtack client`_.

/add_mountpoint
***************
Accessing this endpoint allows you to add a manually created mountpoint to the thumbtack database.

/images
*******
Accessing this endpoint allows you to get information on all of the disk images found in the image directory.

/image_dir
**********
Accessing this endpoint allows you to update or retrieve the path of the current image directory.

/mounts/
********
Accessing this endpoint allows you to get information on all of the disk images that are currently mounted.

/mounts/<path:image_path>
*************************
Gets you information about a specific disk image that is currently mounted. If that disk image is not currently
mounted, it returns a ``404`` error with a message stating that the requested disk image is not mounted.

/supported
**********
This endpoint returns a JSON object containing information about which supporting libraries are installed and
which are not.


.. _thumbtack client: https://github.com/mitre/thumbtack-client
