import imagemounter_mitre.exceptions

from flask import Blueprint, current_app, redirect, render_template, request
from flask_restful import Api

import os

from .exceptions import UnexpectedDiskError, NoMountableVolumesError, DuplicateMountAttemptError, EncryptedImageError, DuplicateVolumeGroupError
from .resources import Mount, SupportedLibraries, Images, ImageDir, ManualMount
from .utils import (
    get_supported_libraries,
    get_images,
    mount_image,
    unmount_image,
    get_ref_count,
    monitor_image_dir,
    add_mountpoint,
    create_key
)

main = Blueprint("thumbtack", __name__)

api = Api(main)
api.add_resource(Mount, "/mounts/<path:image_path>", "/mounts/")
api.add_resource(SupportedLibraries, "/supported", endpoint="supported")
api.add_resource(Images, "/images", endpoint="images")
api.add_resource(ImageDir, "/image_dir")
api.add_resource(ManualMount, "/add_mountpoint", endpoint="add_mountpoint")


@main.route("/", methods=["GET"])
@main.route("/index", methods=["GET"])
def index():
    image_dir = current_app.config["IMAGE_DIR"]
    supported_mount_types = []
    unsupported_mount_types = []

    supported_libraries = get_supported_libraries()

    for mount_type, supported in supported_libraries.items():
        if supported:
            supported_mount_types.append(mount_type)
        else:
            unsupported_mount_types.append(mount_type)

    current_app.logger.debug("-------------- Getting images!!! --------------")
    # On refresh, update DB to match what's on disk
    monitor_image_dir()
    images = get_images()
    current_app.logger.debug("-------------- Got images!!! --------------")

    return render_template(
        "index.html",
        supported_mount_types=supported_mount_types,
        unsupported_mount_types=unsupported_mount_types,
        image_dir=image_dir,
        images=images,
    )


@main.route("/mount_form", methods=["POST"])
def mount_form():
    rel_path = request.form["img_to_mount"]
    operation = request.form["operation"]

    status = None

    if operation == "mount":
        decryption_method = request.form["decryption method"]
        key = request.form["key"]

        key_dict = create_key(decryption_method, key)
        creds = {}
        if key_dict:
            for i in range(0, 25):
                creds[i] = key_dict["key"]
        else:
            creds = None

        mounted_disk = None
        duplicate_vg = False
        try:
            mounted_disk = mount_image(rel_path, creds)
        except imagemounter_mitre.exceptions.SubsystemError:
            current_app.logger.error("imagemounter was unable to mount: {}", rel_path)
            status = f"Thumbtack was unable to mount {rel_path} using the imagemounter Python library."
        except PermissionError:
            current_app.logger.error(
                "Permission error! Are you running with root privileges?"
            )
            status = f"Thumbtack does not have mounting privileges for {rel_path}. Are you running as root?"
        except UnexpectedDiskError:
            status = "Unexpected number of disks. Thumbtack can only handle disk images that contain one disk."
        except NoMountableVolumesError:
            status = f"No volumes in {rel_path} were able to be mounted."
        except EncryptedImageError as e:
            status = e
        except NotADirectoryError:
            status = "Mount failed. Thumbtack server has no mount directory set."
        except DuplicateMountAttemptError:
            status = "Mount attempt is already in progress for this image. Please wait until the current mount attempt completes."
        except DuplicateVolumeGroupError as e:
            status = f"Unable to mount all volumes. Found duplicate volume group name: {str(e)}. Deactivate the volume group and remount the image."
            duplicate_vg = True
        if mounted_disk and mounted_disk.mountpoint is not None:
            if duplicate_vg:
                status = ' '.join(["Mounted Successfully.", status])
            status = "Mounted successfully"

    elif operation == "unmount":

        if unmount_image(rel_path):
            status = "Unmounted successfully"
        else:
            ref_count = get_ref_count(rel_path)
            status = f"{rel_path} is still mounted. Reference count is: {ref_count}"

    else:
        current_app.logger.error("Unknown operation! How did you even get here!?")
        return redirect("/")

    if not status:
        status = "Unable to complete operation"

    return render_template("form_complete.html", status=status)

@main.route("/add_mountpoint_form", methods=["POST"])
def add_mountpoint_form():
    rel_path = request.form["img_to_mount"]
    mountpoint_path = request.form["mountpoint_path"]
    operation = request.form["operation"]

    if mountpoint_path is None or mountpoint_path == "":
        status = "No mountpoint provided."
        return render_template("form_complete.html", status=status)
    if operation == "add_mountpoint":
        mounted_disk = add_mountpoint(rel_path, mountpoint_path)
        if mounted_disk:
            status = f"Added mountpoint {mountpoint_path} for image {rel_path}"
            return render_template("form_complete.html", status=status)
        else:
            status = f"Unable to add mountpoint {mountpoint_path} for image {rel_path}"
            return render_template("form_complete.html", status=status)
    elif operation == "mount" or operation == "unmount":
        status = f"Operation \"{operation}\" is not supported for /add_mounpoint."
        current_app.logger.error(f"{status}")
        return render_template("form_complete.html", status=status)
    else:
        current_app.logger.error("Unknown operation!")
        return redirect("/")
