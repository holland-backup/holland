"""
Path utility functions to inspect MySQL files
"""
import logging
import os
from operator import itemgetter
from os.path import abspath, isabs, join, realpath

from holland.core.backup import BackupError
from holland.core.util.path import getmount, relpath

LOG = logging.getLogger(__name__)


class MySQLPathInfo(tuple):
    """Named tuple whose attributes describe the important
    file paths for the files in a MySQL instance.
    """

    __slots__ = ()

    _fields = (
        "datadir",
        "innodb_log_group_home_dir",
        "innodb_log_files_in_group",
        "innodb_data_home_dir",
        "innodb_data_file_path",
        "abs_tablespace_paths",
    )

    def __new__(
        cls,
        datadir,
        innodb_log_group_home_dir,
        innodb_log_files_in_group,
        innodb_data_home_dir,
        innodb_data_file_path,
        abs_tablespace_paths,
    ):
        return tuple.__new__(
            cls,
            (
                datadir,
                innodb_log_group_home_dir,
                innodb_log_files_in_group,
                innodb_data_home_dir,
                innodb_data_file_path,
                abs_tablespace_paths,
            ),
        )

    @classmethod
    def _make(cls, iterable, new=tuple.__new__):
        "Make a new MySQLPathInfo object from a sequence or iterable"
        result = new(cls, iterable)
        if len(result) != 6:
            raise TypeError("Expected 6 arguments, got %d" % len(result))
        return result

    def __repr__(self):
        return (
            "MySQLPathInfo(datadir=%r, innodb_log_group_home_dir=%r, \
                innodb_log_files_in_group=%r, innodb_data_home_dir=%r, \
                innodb_data_file_path=%r, abs_tablespace_paths=%r)"
            % self
        )

    @staticmethod
    def _asdict(tmp):
        "Return a new dict which maps field names to their values"
        return {
            "datadir": tmp[0],
            "innodb_log_group_home_dir": tmp[1],
            "innodb_log_files_in_group": tmp[2],
            "innodb_data_home_dir": tmp[3],
            "innodb_data_file_path": tmp[4],
            "abs_tablespace_paths": tmp[5],
        }

    def _replace(self, **kwds):
        "Return a new MySQLPathInfo object replacing specified fields with new values"
        result = self._make(
            list(
                map(
                    kwds.pop,
                    (
                        "datadir",
                        "innodb_log_group_home_dir",
                        "innodb_log_files_in_group",
                        "innodb_data_home_dir",
                        "innodb_data_file_path",
                        "abs_tablespace_paths",
                    ),
                    self,
                )
            )
        )
        if kwds:
            raise ValueError("Got unexpected field names: %r" % list(kwds.keys()))
        return result

    def __getnewargs__(self):
        return tuple(self)

    datadir = property(itemgetter(0))
    innodb_log_group_home_dir = property(itemgetter(1))
    innodb_log_files_in_group = property(itemgetter(2))
    innodb_data_home_dir = property(itemgetter(3))
    innodb_data_file_path = property(itemgetter(4))
    abs_tablespace_paths = property(itemgetter(5))

    @classmethod
    def from_mysql(cls, mysql):
        """Create a MySQLPathInfo instance from a live MySQL connection"""
        ibd_homedir = mysql.show_variable("innodb_data_home_dir")
        abs_tablespace_paths = bool(ibd_homedir == "")
        return cls(
            datadir=mysql.show_variable("datadir"),
            innodb_log_group_home_dir=mysql.show_variable("innodb_log_group_home_dir"),
            innodb_log_files_in_group=mysql.show_variable("innodb_log_files_in_group"),
            innodb_data_home_dir=ibd_homedir,
            innodb_data_file_path=mysql.show_variable("innodb_data_file_path"),
            abs_tablespace_paths=abs_tablespace_paths,
        )

    def get_innodb_logdir(self):
        """Determine the directory for innodb's log files"""
        if isabs(self.innodb_log_group_home_dir):
            logdir = self.innodb_log_group_home_dir
        else:
            logdir = join(self.datadir, self.innodb_log_group_home_dir)

        return abspath(realpath(logdir))

    def get_innodb_datadir(self):
        """Determine the base directory for innodb shared tablespaces"""
        ibd_home_dir = self.innodb_data_home_dir or ""
        if not ibd_home_dir or not isabs(ibd_home_dir):
            ibd_home_dir = join(self.datadir, ibd_home_dir)

        return abspath(realpath(ibd_home_dir))

    def walk_innodb_shared_tablespaces(self):
        """Iterate over InnoDB shared tablespace paths"""
        ibd_homedir = self.get_innodb_datadir()
        ibd_data_file_path = self.innodb_data_file_path

        for spec in ibd_data_file_path.split(";"):
            tblspc_path = spec.split(":")[0]
            if not self.abs_tablespace_paths or not isabs(tblspc_path):
                tblspc_path = join(ibd_homedir, tblspc_path)
            yield abspath(realpath(tblspc_path))

    def walk_innodb_logs(self):
        """Iterate over InnoDB redo log paths"""
        basedir = self.get_innodb_logdir()
        for logid in range(self.innodb_log_files_in_group):
            yield join(basedir, "ib_logfile" + str(logid))

    @staticmethod
    def remap_path(path, mountpoint):
        """Remap a path to a new mountpoint

        >>> remap_path('/mnt/raid10/foo/bar/baz', '/mnt/snapshot')
        '/mnt/snapshot/foo/bar/baz'
        """
        rpath = relpath(path, getmount(path))
        return os.path.join(mountpoint, rpath)

    def remap_tablespaces(self, mountpoint):
        """Remap innodb-data-file-path paths to a new mountpoint

        innodb-data-file-path = /mnt/raid/ibdata/ibdata1:10M:autoextend
        >>> remap_tablespaces('/mnt/snapshot/')
        '/mnt/snapshot/ibdata/ibdata1:10M:autoextend'
        """
        innodb_data_home_dir = self.innodb_data_home_dir
        innodb_data_file_path = self.innodb_data_file_path
        spec_list = []
        for spec in innodb_data_file_path.split(";"):
            name, rest = spec.split(":", 1)
            if innodb_data_home_dir == "" and isabs(name):
                name = self.remap_path(name, mountpoint)
            spec = ":".join([name, rest])
            spec_list.append(spec)
        return ";".join(spec_list)


def is_subdir(path, start):
    """Check if path is a subdirectory or some starting path"""
    path = os.path.abspath(path)
    start = os.path.abspath(start)
    end = os.path.basename(path)
    while path != start and end:
        path, end = os.path.split(path)
    return path == start


def check_innodb(pathinfo, ensure_subdir_of_datadir=False):
    """Check that all tablespaces are in the datadir and filesystem"""
    is_unsafe_for_lvm = False
    is_unsafe_for_physical_backups = False
    datadir = realpath(pathinfo.datadir)
    datadir_mp = getmount(datadir)
    for tablespace in pathinfo.walk_innodb_shared_tablespaces():
        space_mp = getmount(tablespace)
        if space_mp != datadir_mp:
            LOG.error(
                "InnoDB shared tablespace %s is not on the same filesystem as the datadir %s",
                tablespace,
                datadir,
            )
            is_unsafe_for_lvm = True
        if ensure_subdir_of_datadir and not is_subdir(tablespace, datadir):
            LOG.error(
                "InnoDB shared tablespace %s is not within a subdirectory of the datadir %s.",
                tablespace,
                datadir,
            )
            is_unsafe_for_physical_backups = True
    ib_logdir = pathinfo.get_innodb_logdir()
    ib_logdir_mp = getmount(ib_logdir)

    if ib_logdir_mp != datadir_mp:
        LOG.error(
            "innodb-log-group-home-dir %s is not on the same filesystem as the MySQL datadir %s",
            ib_logdir,
            datadir,
        )
        is_unsafe_for_lvm = True
    if ensure_subdir_of_datadir and not is_subdir(ib_logdir, datadir):
        LOG.error(
            "innodb-log-group-home-dir %s is not a subdirectory of the datadir %s.",
            ib_logdir,
            datadir,
        )
        is_unsafe_for_physical_backups = True

    if is_unsafe_for_lvm:
        raise BackupError(
            "One or more InnoDB file paths are not on the same "
            "logical volume as the datadir.  This is unsafe for "
            "LVM snapshot backups."
        )
    if is_unsafe_for_physical_backups:
        raise BackupError(
            "One or more InnoDB files are not contained within "
            "the MySQL datadir. A consistent filesystem backup "
            "is not supported with this configuration in the "
            "current plugin version."
        )
