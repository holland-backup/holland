"""
Plugin for the Holland backup framework
to backup MySQL databases using mysqldump
"""

import os
import re
import subprocess
import tempfile
import shutil
import logging

from holland.lib.mysql.client import MySQLClient
from holland.lib.mysql.option import make_mycnf
from holland.core.util.path import format_bytes, disk_free
from holland.lib.which import which, WhichError

LOGGER = logging.getLogger(__name__)

# We validate our config against the following spec
CONFIGSPEC = """
[maatkit]
lock-method         = option('flush-lock', 'lock-tables', 'none', default='flush-lock')
biggestfirst        = boolean(default=yes)
binlogpos           = boolean(default=yes)
charset             = string(default=None)
chunksize           = string(default=None)
databases           = coerced_list(default=None)
dbregex             = string(default=None)
ignoredb            = coerced_list(default=None)
ignoreengine        = coerced_list(default=None)
tables              = coerced_list(default=None)
tblregex            = string(default=None)
ignoretbl           = coerced_list(default=None)
numthread           = string(default=None)
stopslave           = boolean(default=None)
flushlog            = boolean(default=None)
gzip                = boolean(default=yes)
setperdb            = boolean(default=no)

[mysql:client]
defaults-extra-file = coerced_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(default=None)
""".splitlines()

# Used for our surrogate connection
CLIENT_TIMEOUT = 28800

class BackupError(Exception):
    pass

# This maps old mk-parallel-dump options to the new (1.0.16+) equivalent
NEW_OPTIONS_MAP = {
    'basedir' : 'base-dir',
    'flushlock' : 'flush-lock',
    'locktables' : 'lock-tables',
    'biggestfirst' : 'biggest-first',
    'binlogpos' : 'bin-log-position',
    'chunksize' : 'chunk-size',
    'dbregex' : 'databases-regex',
    'ignoredb' : 'ignore-databases',
    'ignoreengine' : 'ignore-engines',
    'tblregex' : 'tables-regex',
    'ignoretbl' : 'ignore-tables',
    'numthread' : 'threads',
    'stopslave' : 'stop-slave',
    'flushlog' : 'flush-log',
    'setperdb' : 'set-per-database',
    'test' : 'dry-run',
}

def make_compat_args(args):
    result = []
    for arg in args:
        if arg.startswith('--'):
            negate = False
            check_arg = arg[2:] # strip '--'
            if check_arg.startswith('no'):
                check_arg = check_arg[2:] # looking for --no<option>
                negate = True
            if check_arg in NEW_OPTIONS_MAP:
                arg = '--%s%s' % (['','no'][negate], NEW_OPTIONS_MAP[check_arg])
        result.append(arg)
    return result

def maatkit_version(command):
    """Find the version of a maatkit command
    
    Runs the requested command with the --version option
    """
    pid = subprocess.Popen([command, '--version'], 
                           stdout=subprocess.PIPE, 
                           stderr=subprocess.STDOUT, 
                           close_fds=True)
    output, _ = pid.communicate()

    if pid.returncode != 0:
        raise OSError("Failed to run '%s --version' (returncode=%d)" % (command, pid.returncode))

    # mk-parallel-dump  Ver 1.0.16 Distrib 4047 Changeset 4045
    ver_cre = re.compile(r'Changeset (\d+)', re.M)
    match = ver_cre.search(output)
    if not match:
        raise OSError("Could not parse version from Maatkit command %s" % command)
    return int(match.group(1))

class Maatkit(object):
    """
    Maatkit mk-parallel-dump Backup Plugin
    """
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        self.config.validate_config(CONFIGSPEC)
        mycnf_cfg = config.lookup('mysql:client')
        extra_files = map(os.path.expanduser, mycnf_cfg.pop('defaults-extra-file'))
        self.my_cnf = make_mycnf(client=mycnf_cfg, *extra_files)
        self.my_cnf.path = os.path.join(self.target_directory, 'my.cnf')
        if not self.dry_run:
            self.my_cnf.write(self.my_cnf.path)

    def estimate_backup_size(self):
        # PITA
        # Look all all the filtering crap in Maatkit and try to get as close 
        # as possible to how Maatkit finds tables
        # options:
        # databases,ignoredb,dbregex
        # tables,ignoretbl,tblregex
        # ignoreengine
        databases = self.config.lookup('maatkit.databases')
        ignoredb = self.config.lookup('maatkit.ignoredb')
        dbregex = self.config.lookup('maatkit.dbregex')
        tables = self.config.lookup('maatkit.tables')
        ignoretbl = self.config.lookup('maatkit.ignoretbl')
        tblregex = self.config.lookup('maatkit.tblregex')
        ignoreengine = self.config.lookup('maatkit.ignoreengine')
        
        if self.dry_run:
            if 'password' in self.my_cnf['client']:
                password = self.my_cnf['client'].pop('password')
                self.my_cnf['client']['passwd'] = password
            mysqlclient = MySQLClient(**dict(self.my_cnf['client'].items()))
        else:
            mysqlclient = MySQLClient(read_default_file=self.my_cnf.path)
        estimated_size = 0
        for db in mysqlclient.show_databases():
            for info in mysqlclient.show_table_status(db):
                tbl = info['name']
                qtbl = db + '.' + tbl
                
                if databases and db not in databases:
                    continue
                if ignoredb and db in ignoredb:
                    continue
                if dbregex and not re.search(dbregex, db):
                    continue
                if tables and (tbl not in tables or qtbl not in tables):
                    continue
                if ignoretbl and (tbl in ignoretbl or qtbl in ignoretbl):
                    continue
                if tblregex and not re.search(tblregex, qtbl):
                    continue
                if ignoreengine and info['engine'] in ignoreengine:
                    continue
                    
                estimated_size += int(info['data_length'] or 0) + \
                                    int(info['index_length'] or 0)
        return estimated_size
        
    def backup(self):
        """
        Start a backup.  This attempts one or more mysqldump
        runs.  On error, a BackupError exception will be thrown.
        """
        args = self._build_args()
        if maatkit_version('mk-parallel-dump') >= 3712:
            args = make_compat_args(args)
        LOGGER.info("mk-parallel-dump %s", ' '.join(args))
        mk_pdump = which('mk-parallel-dump')
        pid = subprocess.Popen([mk_pdump] + args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for line in pid.stdout:
            LOGGER.info(line.rstrip())
        for line in pid.stderr:
            LOGGER.error(line.rstrip())
        status = pid.wait()
        if status != 0:
            LOGGER.error("mk-parallel-dump failed (status=%d)", status)
            raise BackupError("mk-parallel-dump exited with %d" % status)
            
    def cleanup(self):
        """
        Finish a backup.
        """
        try:
            os.unlink(self.my_cnf)
        except:
            pass

    def _build_args(self):
        args = []
        
        args += ['--defaults-file', self.my_cnf.path]
        args += ['--basedir', os.path.join(self.target_directory, 'backup_data')]
                
        if self.dry_run:
            args += ['--test']
            
        lock_method = self.config.lookup('maatkit.lock-method')
        if lock_method == 'flush-lock':
            args.append('--flushlock')
        elif lock_method == 'lock-tables':
            args.append('--locktables')
        elif lock_method == 'none':
            args.append('--noflushlock')
        
        self._build_kv_args(args)
        self._build_bool_args(args)
        self._build_neg_args(args)

        return args

    def _build_kv_args(self, args):
        """
        Construct Maakit options that take an argument
        """
        properties = [
            'maatkit.charset',
            'maatkit.chunksize',
            'maatkit.databases',
            'maatkit.dbregex',
            'maatkit.ignoredb',
            'maatkit.tables',
            'maatkit.tblregex',
            'maatkit.ignoretbl',
            'maatkit.ignoreengine',
            'maatkit.numthread'
        ]
        
        for prop in properties:
            val = self.config.lookup(prop)
            if val:
                if isinstance(val, (list,tuple)):
                    val = ','.join(val)
                key = prop.split('.')[1]
                args.append('--%s' % key)
                args.append(str(val))

    def _build_bool_args(self, args):
        """
        Construct mk-parallel-dump options that
        take no argument and are simply boolean
        """
        properties = [
            'maatkit.flushlog',
            'maatkit.stopslave',
            'maatkit.setperdb'
        ]
        
        for prop in properties:
            val = self.config.lookup(prop)
            if val:
                key = prop.split('.')[1]
                args.append('--%s' % key)
    
    def _build_neg_args(self, args):
        """
        Construct mk-parallel-dump options that
        are negatable (disable default behavior)
        """
        properties = [
            'maatkit.biggestfirst',
            'maatkit.binlogpos',
            'maatkit.gzip',
        ]
        
        for prop in properties:
            val = self.config.lookup(prop)
            if not val:
                key = prop.split('.')[1]
                args.append('--no%s' % key)
        
def provider(*args, **kwargs):
    return Maatkit(*args, **kwargs)
