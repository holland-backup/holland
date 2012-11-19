"""MySQL option files support

http://dev.mysql.com/doc/refman/5.1/en/option-files.html
"""
import os, sys
import re
import errno
import codecs
import logging
import subprocess
from holland.lib.mysql.option.parser import OptionFile

LOG = logging.getLogger(__name__)

def merge_options(*defaults_files):
    """Merge multiple defaults files together"""
    defaults_config = dict(client={})
    def merge(dst_dict, src_dict):
        """Merge two dictionaries non-destructively"""
        for key, val in src_dict.items():
            if (key in dst_dict and isinstance(dst_dict[key], dict) and
                                isinstance(val, dict)):
                merge(dst_dict[key], val)
            else:
                dst_dict[key] = val

    for config in defaults_files:
        try:
            _my_config = load_options(config)
            merge(defaults_config, _my_config)
        except IOError:
            if not os.path.exists(config):
                LOG.warn("No such file or directory: '%s'", config)
            else:
                raise

    return { 'client' : defaults_config['client'] }

def load_options(path):
    """Load mysql option file from path"""
    options = OptionFile()
    options.read([path])
    return options

def quote(value):
    """Added quotes around a value"""

    return '"' + value.replace('"', '\\"') + '"'

def write_options(config, filename):
    if isinstance(filename, basestring):
        filename = codecs.open(filename, 'w', 'utf8')
    for section in config:
        print >>filename, "[%s]" % section
        for key in config[section]:
            value = unicode(config[section][key])
            print >>filename, "%s = %s" % (key, quote(value))
    filename.close()

def build_mysql_config(mysql_config):
    """Given a standard Holland [mysql:client] section build an in-memory
    config that represents the auth parameters, including those merged in from
    *defaults-extra-files*

    :param mysql_config: required.  This should be a dict object with the
                         zero or more of the following keys:
                           user (string)
                           password (string)
                           host (string)
                           socket (string)
                           port (integer)
                           defaults-extra-file (list)
    :type mysql_config: dict
    """
    defaults_config = merge_options(*mysql_config['defaults-extra-file'])

    if mysql_config.get('password') is not None:
        password = mysql_config['password']
        if password.startswith('file:'):
            password_file = password[len('file:'):]
            password = process_password_file(password_file)
            mysql_config['password'] = password
            LOG.info("Read password from file '%s'", password_file)

    for key in ('user', 'password', 'socket', 'host', 'port'):
        if key in mysql_config and mysql_config[key]:
            defaults_config['client'][key] = mysql_config[key]
    return defaults_config

def process_password_file(path):
    """Read the file at `path` and return the
    contents of the file

    :param path: file path to read a passwrod from
    :returns: password contained in `path`
    """
    try:
        # strip trailing whitespace
        password = open(path, 'r').read().rstrip()
        LOG.debug("Loaded password file %s", path)
        return password
    except IOError, exc:
        LOG.error("Failed to load password file %s: %s", path, str(exc))
        raise
