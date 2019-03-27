import subprocess
import sys

from flask import current_app, request
from flask_restful import Resource, marshal_with, abort, fields

try:
    from pathlib import Path
except ImportError:
    from pathlib2 import Path

from .exceptions import MountManagerError


volume_fields = {
    'size': fields.Integer,
    'offset': fields.Integer,
    'index': fields.Integer,
    'label': fields.String(attribute=lambda obj: obj.info.get('label')),
    'fsdescription': fields.String(attribute=lambda obj: obj.info.get('fsdescription')),
    'fstype': fields.String,
    'mountpoint': fields.String,
}
disk_fields = {
    'name': fields.String(attribute='_name'),
    'imagepath': fields.String(attribute=lambda obj: obj.paths[0]),
    'mountpoint': fields.String,
    'volumes': fields.List(fields.Nested(volume_fields)),
}
disk_mount = {
    'disk_info': fields.Nested(disk_fields),
    'ref_count': fields.Integer
}


class Mount(Resource):
    """A Mount object that allows you to mount and unmount images.

    Attributes
    ----------
    mount_manager : thumbtack.MountManager
        The manager object tracks mounted state for all image
        files used with this Mount object.
    """

    def __init__(self, mount_manager):
        """Create a Mount object.

        Parameters
        ----------
        mount_manager : thumbtack.MountManager
            The manager object used that tracks mounted state
            of image files.
        """
        current_app.logger.info('Instantiating the Mount class')
        self.mount_manager = mount_manager

    @marshal_with(disk_fields)
    def put(self, image_path):
        """Mounts an image file.

        Parameters
        ----------
        image_path : str
            Path to an image file to be mounted. This is
            a relative path from the IMAGE_DIR config variable directory to the file on disk.
        mount_dir : str
            Path where the image file will be mounted.
        """
        try:
            mount_dir = request.args.get('mount_dir', '/mnt/thumbtack')
            print('mount_dir:', mount_dir)
            return self.mount_manager.mount_image(image_path, mount_dir)
        except MountManagerError as e:
            abort(400, message=str(e))

    @marshal_with(disk_mount)
    def get(self, image_path=None):
        """Retrieve information about tracked images.

        Parameters
        ----------
        image_path : str, optional
            Path to an image file.

        Returns
        -------
        dict
            Output from mount_manager.all_mounts() or
            mount_manager.get_mount(`image_path`)
        """
        if not image_path:
            response = []
            all_mounts = self.mount_manager.all_mounts()
            for mount in all_mounts:
                # have to include the trailing slash
                image_dir = '{}/'.format(current_app.config['IMAGE_DIR'])
                rel_path = mount.paths[0].replace(image_dir, '')
                ref_count = self.mount_manager.get_ref_count(rel_path)
                response.append({
                    'disk_info': mount,
                    'ref_count': ref_count
                })
            return response

        disk_info = self.mount_manager.get_mount(image_path)
        ref_count = self.mount_manager.get_ref_count(image_path)
        response = {
            'disk_info': disk_info,
            'ref_count': ref_count
        }
        return response

    def delete(self, image_path):
        """Unmounts an image file.

        Parameters
        ----------
        image_path : str
            Path to an image file to unmount. This is
            an absolute path to the file on disk.
        """
        self.mount_manager.unmount_image(image_path)


class SupportedLibraries(Resource):

    def get(self):

        virtualenv_bin_directory = Path(sys.argv[0]).parent
        imount_cmd = str(virtualenv_bin_directory / 'imount')

        # TODO: this seems... not right
        # gunicorn_powered = True if str(Path(sys.argv[0]).name) == 'gunicorn' else False
        # if gunicorn_powered:
        #     current_app.logger.info('powered by gunicorn')
        #     imount_cmd = str(Path(sys.argv[0]).parent / 'imount')

        run_args = [imount_cmd, '--check']

        current_app.logger.info(run_args)
        output = subprocess.check_output(run_args).decode().split('\n')
        outputjson = {}

        for line in output:
            lineSplit = line.split()
            if len(lineSplit) > 0 and ('MISSING' in lineSplit or 'INSTALLED' in lineSplit):
                if lineSplit[0] == 'INSTALLED':
                    outputjson[str(lineSplit[1])] = True
                else:
                    outputjson[str(lineSplit[1])] = False

        return outputjson
