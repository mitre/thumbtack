import imagemounter.exceptions

from flask import Blueprint, current_app, redirect, render_template, request

from .utils import get_supported_libraries, get_images, mount_image, unmount_image, get_ref_count
from .exceptions import UnexpectedDiskError, NoMountableVolumesError

main = Blueprint('', __name__)


@main.route('/', methods=['GET'])
@main.route('/index', methods=['GET'])
def index():
    image_dir = current_app.config['IMAGE_DIR']
    supported_mount_types = []
    unsupported_mount_types = []

    supported_libraries = get_supported_libraries()

    for mount_type, supported in supported_libraries.items():
        if supported:
            supported_mount_types.append(mount_type)
        else:
            unsupported_mount_types.append(mount_type)

    images = get_images()

    return render_template('index.html',
                           supported_mount_types=supported_mount_types,
                           unsupported_mount_types=unsupported_mount_types,
                           image_dir=image_dir,
                           images=images)


@main.route('/mount_form', methods=['POST'])
def mount_form():
    rel_path = request.form['img_to_mount']
    operation = request.form['operation']

    status = None

    if operation == 'mount':

        mounted_disk = None
        try:
            mounted_disk = mount_image(rel_path)
        except imagemounter.exceptions.SubsystemError:
            current_app.logger.error('imagemounter was unable to mount: {}', rel_path)
            status = 'Thumbtack was unable to mount {} using the imagemounter Python library.'.format(rel_path)
        except PermissionError:
            current_app.logger.error('Permission error! Are you running with root privileges?')
            status = 'Thumbtack does not have mounting privileges for {}. Are you running as root?'.format(rel_path)
        except UnexpectedDiskError:
            status = 'Unexpected number of disks. Thumbtack can only handle disk images that contain one disk.'
        except NoMountableVolumesError:
            status = 'No volumes in {} were able to be mounted.'.format(rel_path)

        if mounted_disk and mounted_disk.mountpoint is not None:
            status = 'Mounted successfully'

    elif operation == 'unmount':

        if unmount_image(rel_path):
            status = 'Unmounted successfully'
        else:
            ref_count = get_ref_count(rel_path)
            status = '{} is still mounted. Reference count is: {}'.format(rel_path, ref_count)

    else:
        current_app.logger.error('Unknown operation! How did you even get here!?')
        return redirect('/')

    if not status:
        status = 'Unable to complete operation'

    return render_template('form_complete.html',
                           status=status)

