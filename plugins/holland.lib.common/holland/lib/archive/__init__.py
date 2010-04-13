from dir_archive import DirArchive
from tar_archive import TarArchive
from zip_archive import ZipArchive

__all__ = [
    'DirArchive',
    'TarArchive',
    'ZipArchive'
]

archive_methods = {
    'dir' : (DirArchive, ''),
    'tar' : (TarArchive, '.tgz'),
    'zip' : (ZipArchive, '.zip')
}

def create_archive(method, base_path):
    archive_info = archive_methods.get(method)
    
    if not archive_info:
        raise LookupError("Unsupported archive method: %r" % method)
    
    cls, ext = archive_info
    
    if not base_path.endswith(ext):
        base_path += ext
    
    return cls(base_path)
