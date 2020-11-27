import imagemounter.exceptions

from flask import current_app
from flask_restful import Resource, marshal_with, abort, fields

from .exceptions import (
    UnexpectedDiskError,
    NoMountableVolumesError,
    ImageNotInDatabaseError,
)
from .utils import get_mount_info, get_supported_libraries, mount_image, unmount_image

volume_fields = {
    "size": fields.Integer,
    "offset": fields.Integer,
    "index": fields.Integer,
    "label": fields.String(attribute=lambda obj: obj.info.get("label")),
    "fsdescription": fields.String(attribute=lambda obj: obj.info.get("fsdescription")),
    "fstype": fields.String,
    "mountpoint": fields.String,
}
disk_fields = {
    "name": fields.String(attribute="_name"),
    "imagepath": fields.String(attribute=lambda obj: obj.paths[0]),
    "mountpoint": fields.String,
    "volumes": fields.List(fields.Nested(volume_fields)),
}
disk_mount = {"disk_info": fields.Nested(disk_fields), "ref_count": fields.Integer}


class Mount(Resource):
    """A Mount object that allows you to mount and unmount images.
    """

    def __init__(self):
        """Create a Mount object.
        """
        current_app.logger.debug("Instantiating the Mount class")

    @marshal_with(disk_fields)
    def put(self, image_path):
        """Mounts an image file.

        Parameters
        ----------
        image_path : str
            Relative path to an image file to be mounted.
            This is relative to the Thumbtack server's IMAGE_DIR config variable.
        """
        status = None
        try:
            mounted_disk = mount_image(image_path)

            if mounted_disk and mounted_disk.mountpoint is not None:
                current_app.logger.info(f"Image mounted successfully: {image_path}")
                return mounted_disk

        # TODO: refactor to not duplicate code in the mount_form in views.py
        except imagemounter.exceptions.SubsystemError:
            status = f"Thumbtack was unable to mount {image_path} using the imagemounter Python library."
        except PermissionError:
            status = f"Thumbtack does not have mounting privileges for {image_path}. Are you running as root?"
        except UnexpectedDiskError:
            status = "Unexpected number of disks. Thumbtack can only handle disk images that contain one disk."
        except NoMountableVolumesError:
            status = f"No volumes in {image_path} were able to be mounted."
        except ImageNotInDatabaseError:
            status = f"Cannot mount {image_path}. Image is not in Thumbtack database."

        current_app.logger.error(status)
        abort(400, message=str(status))

    @marshal_with(disk_mount)
    def get(self, image_path=None):
        """Retrieve information about tracked images.

        Parameters
        ----------
        image_path : str, optional
            Relative path to an image file.

        Returns
        -------
        dict
            Dictionary of useful information about a mounted disk image or a list of all mounted images.
        """
        mount_info = get_mount_info(image_path)
        if not mount_info:
            # empty list -- nothing mounted -- is ok to return
            if isinstance(mount_info, list):
                return mount_info
            abort(404, message=f"{image_path} not mounted")
        return mount_info

    def delete(self, image_path):
        """Unmounts an image file.

        Parameters
        ----------
        image_path : str
            Relative path to an image file to unmount.
        """
        unmount_image(image_path)


class SupportedLibraries(Resource):
    def get(self):
        return get_supported_libraries()
