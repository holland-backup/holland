"""MySQL option files support

http://dev.mysql.com/doc/refman/5.1/en/option-files.html
"""
import os, sys
import re
import codecs
import logging
import subprocess

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
        _my_config = load_options(config)
        merge(defaults_config, _my_config)

    return defaults_config

def canonicalize_option(option):
    known = [
        'host',
        'password',
        'port',
        'socket',
        'user',
    ]

    candidates = []

    for key in known:
        if key.startswith(option):
            candidates.append(key)

    if len(candidates) > 1:
        raise ValueError("ambiguous option '%s' (%s)" %
                         (option, ','.join(candidates)))

    if not candidates:
        raise ValueError("unknown option '%s'" % (option))

    return candidates[0]

def load_options(path, my_print_defaults='my_print_defaults'):
    """Load mysql option file from path"""
    args = [
        my_print_defaults,
        '--defaults-file=%s' % path,
        'client',
    ]
    process = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               close_fds=True)
    data, errors = process.communicate()

    if process.returncode != 0:
        raise ValueError(errors)

    cfg = {}
    for line in data.splitlines():
        opt, value = line.split('=', 1)
        # skip -- in opt and canonicalize it
        opt = canonicalize_option(opt[2:]) 
        cfg[opt] = value

    return { 'client' : cfg }

def quote(value):
    """Added quotes around a value"""

    return '"' + value.replace('"', '\\"') + '"'

def write_options(config, filename):
    if isinstance(filename, basestring):
        filename = codecs.open(filename, 'w', 'utf8')
    for section in config:
        print >>filename, "[%s]" % section
        for key in config[section]:
            value = str(config[section][key])
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
            LOG.info("Read password from file %r", password_file)

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
