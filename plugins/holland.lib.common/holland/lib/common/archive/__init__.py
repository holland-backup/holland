"""
Archive
"""

from .dir_archive import DirArchive
from .tar_archive import TarArchive
from .zip_archive import ZipArchive

__all__ = ["DirArchive", "TarArchive", "ZipArchive"]

ARCHIVE_METHODS = {
    "dir": (DirArchive, ""),
    "tar": (TarArchive, ".tgz"),
    "zip": (ZipArchive, ".zip"),
}


def create_archive(method, base_path):
    """
    Create Archive
    """
    archive_info = ARCHIVE_METHODS.get(method)

    if not archive_info:
        raise LookupError("Unsupported archive method: %r" % method)

    cls, ext = archive_info

    if not base_path.endswith(ext):
        base_path += ext

    return cls(base_path)
