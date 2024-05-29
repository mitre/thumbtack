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
