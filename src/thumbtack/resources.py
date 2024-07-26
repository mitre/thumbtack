import imagemounter_mitre.exceptions
import os

from flask import current_app, request
from flask_restful import Resource, marshal_with, abort, fields

from .exceptions import (
    UnexpectedDiskError,
    NoMountableVolumesError,
    ImageNotInDatabaseError,
    DuplicateMountAttemptError,
    EncryptedImageError,
    DuplicateVolumeGroupError,
)
from .utils import get_mount_info, get_supported_libraries, mount_image, unmount_image, get_images, add_mountpoint

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
    "paths": fields.Raw(attribute=lambda obj: obj._paths, default=None)
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

        # Create volume-key mapping. Need to find a better appraoch for this
        creds = {}
        if len(request.args.getlist("key")) > 0:
            for i in range(0, 25):
                creds[i] = request.args.getlist("key")[0]
        else:
            creds = None

        try:
            current_app.mnt_mutex.acquire()
            mounted_disk = mount_image(image_path, creds=creds)

            if mounted_disk and mounted_disk.mountpoint is not None:
                current_app.logger.info(f"Image mounted successfully: {image_path}")
                current_app.mnt_mutex.release()
                return mounted_disk

        # TODO: refactor to not duplicate code in the mount_form in views.py
        except imagemounter_mitre.exceptions.SubsystemError:
            status = f"Thumbtack was unable to mount {image_path} using the imagemounter Python library."
        except PermissionError:
            status = f"Thumbtack does not have mounting privileges for {image_path}. Are you running as root?"
        except UnexpectedDiskError:
            status = "Unexpected number of disks. Thumbtack can only handle disk images that contain one disk."
        except NoMountableVolumesError:
            status = f"No volumes in {image_path} were able to be mounted."
        except ImageNotInDatabaseError:
            status = f"Cannot mount {image_path}. Image is not in Thumbtack database."
        except EncryptedImageError:
            status = f"Unable to mount encrypted image."
        except DuplicateMountAttemptError:
            status = "Mount attempt is already in progress for this image. Please wait until the current mount attempt completes."
        except DuplicateVolumeGroupError as e:
            status = f"Unable to mount all volumes. Found duplicate volume group name: {str(e)}. Deactivate the volume group and remount the image."

        current_app.mnt_mutex.release()
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

    def delete(self, image_path=None):
        """Unmounts an image file.

        Parameters
        ----------
        image_path : str
            Relative path to an image file to unmount.
        """
        current_app.mnt_mutex.acquire()
        unmount_image(image_path)
        current_app.mnt_mutex.release()


class SupportedLibraries(Resource):
    def get(self):
        return get_supported_libraries()

class Images(Resource):
    def get(self):
        images = get_images()
        # Remove non-serializable parser for api call
        for image in images:
            if "parser" in image:
                image.pop("parser")
        return images

class ImageDir(Resource):
    def put(self):
        image_dir = request.args.getlist("image_dir")[0]
        current_app.config.update(IMAGE_DIR=image_dir)
        return image_dir
    def get(self):
        return current_app.config["IMAGE_DIR"]

class ManualMount(Resource):
    """Mount object that allows users to manually create and add a mountpoint."""

    def __init__(self):
        pass

    def put(self):
        """Adds mountpoint to thumbtack database.

        Parameters
        ----------
        mountpoint_path : str
            Absolute path where the image is mounted
        """

        image_path = request.args.getlist("image_path")[0]
        mountpoint_path = request.args.getlist("mountpoint_path")[0]

        if mountpoint_path is None or mountpoint_path == "":
            status = "No mountpoint provided."
            current_app.logger.error(status)
            abort(400, message=str(status))
        if not os.path.isdir(mountpoint_path):
            status = f"Could not find {mountpoint_path}. Ensure the mountpoint exists before adding it to thumbtack."
            current_app.logger.error(status)
            abort(400, message=str(status))

        mounted_disk = add_mountpoint(image_path, mountpoint_path)
        if mounted_disk:
            status = f"Added mountpoint {mountpoint_path} for image {image_path}"
            return mountpoint_path
        else:
            status = f"Unable to add mountpoint {mountpoint_path} for image {image_path}"
            current_app.logger.error(status)
            abort(400, message=str(status))

