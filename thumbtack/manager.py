from collections import namedtuple

import imagemounter
import os
from flask import current_app
from flask_restful import abort

from .exceptions import MountManagerError


class MountManager(object):
    """Built from an `ImageParser <http://imagemounter.readthedocs.io/en/latest/python.html#imageparser>`_ object, the
    MountManager object tracks the mounted state for all image files used with the object.

    Attributes
    ----------
    ImageParser : imagemounter.ImageParser
        The root object of the `imagemounter <http://imagemounter.readthedocs.io/en/latest/python.html#imageparser>`_ Python interface.
        The ImageParser object has access to all functions in the imagemounter.parser.py
        module.
    """
    MountInfo = namedtuple('MountInfo', ('parser', 'ref_count'))

    def __init__(self):
        self.mounts = {}

    def mount_image(self, relative_image_path, mount_dir='/mnt/thumbtack'):
        """
           First checks if the image is already mounted,
           then verifies that the file path is valid.

        Parameters
        ----------
        relative_image_path : str
            Path to an image file. This is a relative path to the file on disk from the IMAGE_DIR.
        mount_dir : str
            Path where the image file will be mounted.

        Returns
        -------
        An imagemounter.ImageParser.Disk object
            the `imagemounter.Disk <http://imagemounter.readthedocs.io/en/latest/python.html#disk>`_ just mounted

        """
        full_image_path = '{}/{}'.format(current_app.config['IMAGE_DIR'], relative_image_path)

        # See if this image is already mounted
        mount_info = self.mounts.get(relative_image_path)
        if mount_info is not None:
            new_ref_count = mount_info.ref_count + 1
            current_app.logger.info(
                'MountManager.mount_image: image_path "{}" is already mounted. Increasing ref count to {:d}.'.format(
                    relative_image_path, new_ref_count))
            self.mounts[relative_image_path] = self.MountInfo(parser=mount_info.parser, ref_count=new_ref_count)
            return mount_info.parser.disks[0]

        # Verify we have a valid file path
        if not os.access(full_image_path, os.R_OK):
            msg = 'MountManager.mount_image: "{}" is not a valid file or is not accessible for reading'.format(
                relative_image_path)
            current_app.logger.info(msg)
            raise MountManagerError(msg)

        # Mount it
        current_app.logger.info('MountManager.mount_image: mounting image_path "{}"'.format(relative_image_path))
        # Updates: full_image_path needs to be iterable, pretty keeps path names the way they were
        image_parser = imagemounter.ImageParser([full_image_path], pretty=True, mountdir=mount_dir)

        # Volumes won't be mounted unless this generator is iterated
        for _ in image_parser.init():
            pass

        if len(image_parser.disks) != 1:
            current_app.logger.info('MountManager.mount_image: Error: Unexpected number of disks (expected 1, got {:d})'.format(
                len(image_parser.disks)))
            image_parser.clean(allow_lazy=True)
            raise MountManagerError('Unexpected number of disks (expected 1, got {:d})'.format(len(image_parser.disks)))

        current_app.logger.info("MountManager.mount_image: Disk Mounted: {}".format(image_parser.disks[0].mountpoint))
        for volume in image_parser.disks[0].volumes:
            current_app.logger.info("MountManager.mount_image: Volume description: {}".format(volume.get_description()))
            current_app.logger.info("MountManager.mount_image: Volume mountpoint: {}".format(
                volume.mountpoint if volume.mountpoint else '<none>'))

        # Fail if we couldn't mount any of the volumes
        if not [v for v in image_parser.disks[0].volumes if v.mountpoint]:
            image_parser.clean(allow_lazy=True)
            current_app.logger.error('MountManager.mount_image: No mountable volumes in image "{}"'.format(relative_image_path))
            raise MountManagerError('Disk image contains no mountable volumes')

        self.mounts[relative_image_path] = self.MountInfo(parser=image_parser, ref_count=1)
        return image_parser.disks[0]

    def get_mount(self, relative_image_path):
        """Retrieves the disk object at the given image path

            Parameters
            ----------
            image_path : str
                Path to the image file. This is
                an absolute path to the file on disk.
            Returns
            -------
            imagemounter.ImageParser.disk object
                the `imagemounter.Disk <http://imagemounter.readthedocs.io/en/latest/python.html#disk>`_ at the specified image path
        """
        mount_info = self.mounts.get(relative_image_path)
        if mount_info is not None:
            return mount_info.parser.disks[0]
        else:
            abort(404, message='Image path {} is not mounted'.format(relative_image_path))

    def unmount_image(self, relative_image_path):
        """Unmounts by using the supplied image path as an index into the collection of mounted images, and then removes itself from the collection.

        Parameters
        ----------
        image_path : str
            Path to the image file. This is
            an absolute path to the file on disk.

        """
        mount_info = self.mounts.get(relative_image_path)
        if mount_info is None:
            abort(404, message='Image path {} is not mounted'.format(relative_image_path))

        if mount_info.ref_count > 1:
            new_ref_count = mount_info.ref_count - 1
            current_app.logger.info(
                'MountManager.unmount_image: image_path "{}" is still referenced. Decreasing ref count to {:d}.'.format(
                    relative_image_path, new_ref_count))
            self.mounts[relative_image_path] = self.MountInfo(parser=mount_info.parser, ref_count=new_ref_count)
        else:
            current_app.logger.info('MountManager.unmount_image: unmounting image_path "{}"'.format(relative_image_path))
            mount_info.parser.clean(allow_lazy=True)
            del self.mounts[relative_image_path]

    def all_mounts(self):
        """Retrieves disk object for each disk with a valid image path

        Returns
        -------
        imagemounter.ImageParser.Disk objects
            collection of valid `Disk <http://imagemounter.readthedocs.io/en/latest/python.html#disk>`_ objects
            associated with this MountManager

        """
        return [mi.parser.disks[0] for mi in self.mounts.values()]

    def get_ref_count(self, relative_image_path):
        mount_info = self.mounts.get(relative_image_path)
        if mount_info is not None:
            return mount_info.ref_count
        return 0

    def cleanup(self):
        """Uses `imagemounter.ImageParser.clean <http://imagemounter.readthedocs.io/en/latest/python.html#imageparser>`_ to
        unmount Disk objects associated with this MountManger

        """
        current_app.logger.info('MountManager.cleanup: cleaning remaining mounts')
        for image_path, mount_info in self.mounts.iteritems():
            current_app.logger.warning(
                'MountManager.cleanup: image_path "{}" is being unmounted with {:d} outstanding references.'.format(
                    image_path, mount_info.ref_count))
            mount_info.parser.clean(allow_lazy=True)
