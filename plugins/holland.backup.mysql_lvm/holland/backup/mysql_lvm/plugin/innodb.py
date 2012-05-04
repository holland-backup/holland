"""
Path utility functions to inspect MySQL files
"""
import os
from os.path import isabs, join, realpath, abspath, splitext
try:
    from operator import itemgetter
except ImportError:
    def itemgetter(*items):
        if len(items) == 1:
            item = items[0]
            def g(obj):
                return obj[item]
        else:
            def g(obj):
                return tuple(obj[item] for item in items)
        return g

class MySQLPathInfo(tuple):
    """Named tuple whose attributes describe the important
    file paths for the files in a MySQL instance.
    """

    __slots__ = ()

    _fields = ('datadir', 'innodb_log_group_home_dir', 'innodb_log_files_in_group', 'innodb_data_home_dir', 'innodb_data_file_path', 'abs_tablespace_paths')

    def __new__(_cls, datadir, innodb_log_group_home_dir, innodb_log_files_in_group, innodb_data_home_dir, innodb_data_file_path, abs_tablespace_paths):
        return _tuple.__new__(_cls, (datadir, innodb_log_group_home_dir, innodb_log_files_in_group, innodb_data_home_dir, innodb_data_file_path, abs_tablespace_paths))

    #@classmethod
    def _make(cls, iterable, new=tuple.__new__, len=len):
        'Make a new MySQLPathInfo object from a sequence or iterable'
        result = new(cls, iterable)
        if len(result) != 6:
            raise TypeError('Expected 6 arguments, got %d' % len(result))
        return result
    _make = classmethod(_make)

    def __repr__(self):
        return 'MySQLPathInfo(datadir=%r, innodb_log_group_home_dir=%r, innodb_log_files_in_group=%r, innodb_data_home_dir=%r, innodb_data_file_path=%r, abs_tablespace_paths=%r)' % self

    def _asdict(t):
        'Return a new dict which maps field names to their values'
        return {'datadir': t[0], 'innodb_log_group_home_dir': t[1], 'innodb_log_files_in_group': t[2], 'innodb_data_home_dir': t[3], 'innodb_data_file_path': t[4], 'abs_tablespace_paths': t[5]}

    def _replace(_self, **kwds):
        'Return a new MySQLPathInfo object replacing specified fields with new values'
        result = _self._make(map(kwds.pop, ('datadir', 'innodb_log_group_home_dir', 'innodb_log_files_in_group', 'innodb_data_home_dir', 'innodb_data_file_path', 'abs_tablespace_paths'), _self))
        if kwds:
            raise ValueError('Got unexpected field names: %r' % kwds.keys())
        return result

    def __getnewargs__(self):
        return tuple(self)

    datadir = property(itemgetter(0))
    innodb_log_group_home_dir = property(itemgetter(1))
    innodb_log_files_in_group = property(itemgetter(2))
    innodb_data_home_dir = property(itemgetter(3))
    innodb_data_file_path = property(itemgetter(4))
    abs_tablespace_paths = property(itemgetter(5))

    #@classmethod
    def from_mysql(cls, mysql):
        """Create a MySQLPathInfo instance from a live MySQL connection"""
        ibd_homedir = mysql.var('innodb_data_home_dir')
        abs_tablespace_paths = bool(ibd_homedir == '')
        return cls(
            datadir=mysql.show_variable('datadir'),
            innodb_log_group_home_dir=mysql.show_variable('innodb_log_group_home_dir'),
            innodb_log_files_in_group=mysql.show_variable('innodb_log_files_in_group'),
            innodb_data_home_dir=ibd_homedir,
            innodb_data_file_path=mysql.show_variable('innodb_data_file_path'),
            abs_tablespace_paths=abs_tablespace_paths
        )
    from_mysql = classmethod(from_mysql)

    def get_innodb_logdir(self):
        """Determine the directory for innodb's log files"""
        if isabs(self.innodb_log_group_home_dir):
            logdir = self.innodb_log_group_home_dir
        else:
            logdir = join(self.datadir, self.innodb_log_group_home_dir)

        return abspath(realpath(logdir))

    def get_innodb_datadir(self):
        """Determine the base directory for innodb shared tablespaces"""
        ibd_home_dir = self.innodb_data_home_dir or ''
        if not ibd_home_dir or not isabs(ibd_home_dir):
            ibd_home_dir = join(self.datadir, ibd_home_dir)

        return abspath(realpath(ibd_home_dir))

    def walk_innodb_shared_tablespaces(self):
        """Iterate over InnoDB shared tablespace paths"""
        ibd_homedir = self.get_innodb_datadir()
        ibd_data_file_path = self.innodb_data_file_path

        for spec in ibd_data_file_path.split(';'):
            tblspc_path = spec.split(':')[0]
            if not self.abs_tablespace_paths or not isabs(tblspc_path):
                tblspc_path = join(ibd_homedir, tblspc_path)
            yield abspath(realpath(tblspc_path))

    def walk_innodb_logs(self):
        """Iterate over InnoDB redo log paths"""
        basedir = self.get_innodb_logdir()
        for logid in xrange(self.innodb_log_files_in_group):
            yield join(basedir, 'ib_logfile' + str(logid))
