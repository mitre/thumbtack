class NoMountableVolumesError(Exception):
    pass


class UnexpectedDiskError(Exception):
    pass


class ImageNotInDatabaseError(Exception):
    pass

class DuplicateMountAttemptError(Exception):
    pass

class EncryptedImageError(Exception):
    pass

class DuplicateVolumeGroupError(Exception):
    def __init__(self, msg):
        super().__init__(msg)
