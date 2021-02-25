import imagemounter.exceptions

from flask import Blueprint, current_app, redirect, render_template, request
from flask_restful import Api

from .exceptions import UnexpectedDiskError, NoMountableVolumesError
from .resources import Mount, SupportedLibraries
from .utils import (
    get_supported_libraries,
    get_images,
    mount_image,
    unmount_image,
    get_ref_count,
    monitor_image_dir,
)

main = Blueprint("", __name__)

api = Api(main)
api.add_resource(Mount, "/mounts/<path:image_path>", "/mounts/")
api.add_resource(SupportedLibraries, "/supported", endpoint="supported")


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

        mounted_disk = None
        try:
            mounted_disk = mount_image(rel_path)
        except imagemounter.exceptions.SubsystemError:
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
        except NotADirectoryError:
            status = "Mount failed. Thumbtack server has no mount directory set."
        if mounted_disk and mounted_disk.mountpoint is not None:
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
