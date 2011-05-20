"""
holland.lib.archive.tar_archive

Archive implementation for generating tar archives

"""

import os
import pwd
import grp
import time
import tarfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

def _make_tarinfo(name, size):
    """Make a TarInfo instance from a filename"""
    tarinfo = tarfile.TarInfo(name=name)
    tarinfo.size = size
    tarinfo.mtime = time.time()
    tarinfo.mode = 0660
    tarinfo.type = tarfile.REGTYPE
    tarinfo.uid = os.geteuid()
    tarinfo.gid = os.getegid()
    tarinfo.uname = pwd.getpwuid(os.geteuid()).pw_name
    tarinfo.gname = grp.getgrgid(os.getegid()).gr_name
    return tarinfo

class TarArchive(object):
    """
    Read, write, access Tar archives.
    """
    def __init__(self, path, mode='w:gz'):
        """
        Initialize a TarArchive.

        Arguments:

        path -- Path to the archive file
        mode -- Archive mode.  Default: w:gz (write + gzip) (see tarfile)
        """
        self.path = path
        self.mode = mode
        self.archive = tarfile.open(path, mode)

    def add_file(self, path, name):
        """
        Add a file to the archive.

        Arguments:

        path -- Path to file for which to add to archive.
        name -- Name of file (for tarinfo)
        """
        fileobj = open(path, 'r')
        size = os.fstat(fileobj.fileno()).st_size
        tarinfo = _make_tarinfo(name, size)
        self.archive.addfile(tarinfo, fileobj)
        fileobj.close()

    def add_string(self, string, name):
        """
        Add a string to the archive (fake file).

        Arguments:

        string  -- String to add to the archive.
        name    -- Name of the file to save string as.
        """
        tarinfo = _make_tarinfo(name, len(string))
        self.archive.addfile(tarinfo, StringIO(string))

    def list(self):
        """
        List contents of the archive.  Returns a list of member names.
        """
        result = []
        for member in self.archive.getmembers():
            result.append(member.name)
        return result

    def extract(self, name, dest):
        """
        Extract a member from an archive to 'dest' path.

        Arguments:

        name -- Name of the member in the archive to extract.
        dest -- Path to extract member to.
        """
        self.archive.extract(name, dest)

    def close(self):
        """
        Close archive.
        """
        self.archive.close()

if __name__ == '__main__':
    now = time.time()
    xv = TarArchive('foo.tgz', 'w:gz')
    xv.add_string("[mysqldump]\nignore-table=mysql.user\n", "my.cnf")
    xv.add_string("blah", "test/test.MYD")
    xv.add_file("user.frm", "mysql/user.frm")
    xv.add_file("user.MYD", "mysql/user.MYD")
    xv.add_file("user.MYI", "mysql/user.MYI")
    xv.close()
    print (time.time() - now), "seconds"
