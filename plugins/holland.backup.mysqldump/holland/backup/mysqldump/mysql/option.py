"""MySQL option files support

http://dev.mysql.com/doc/refman/5.1/en/option-files.html
"""
import os
import re
import codecs
import logging
from holland.backup.mysqldump.util import INIConfig, BasicConfig
from holland.backup.mysqldump.util.config import update_config
from holland.backup.mysqldump.util.ini import ParsingError

LOG = logging.getLogger(__name__)

def merge_options(path,
                  *defaults_files,
                  **kwargs):
    defaults_config = INIConfig()
    defaults_config._new_namespace('client')
    for config in defaults_files:
        _my_config = load_options(config)
        update_config(defaults_config, _my_config)

    for key in ('user', 'password', 'socket', 'host', 'port'):
        if kwargs.get(key) is not None:
            defaults_config['client'][key] = kwargs[key]
    write_options(defaults_config, path)

def load_options(filename):
    """Load mysql option file from filename"""
    filename = os.path.abspath(os.path.expanduser(filename))
    cfg = INIConfig()
    try:
        cfg._readfp(open(filename, 'r'))
    except ParsingError, exc:
        LOG.debug("Skipping unparsable lines")
        for lineno, line in exc.errors:
            LOG.debug("Ignored line %d: %s", lineno, line.rstrip())

    return client_sections(cfg)

def unquote(value):
    """Remove quotes from a string."""
    if len(value) > 1 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]

    # substitute meta characters per:
    # http://dev.mysql.com/doc/refman/5.0/en/option-files.html
    MYSQL_META = {
        'b' : "\b",
        't' : "\t",
        'n' : "\n",
        'r' : "\r",
        '\\': "\\",
        's' : " ",
        '"' : '"',
    }
    return re.sub(r'\\(["btnr\\s])',
                  lambda m: MYSQL_META[m.group(1)],
                  value)

def quote(value):
    """Added quotes around a value"""

    return '"' + value.replace('"', '\\"') + '"'

def client_sections(config):
    """Create a copy of config with only valid client auth sections

    This includes [client], [mysql] and [mysqldump] with only options
    related to mysql authentication.
    """

    clean_cfg = INIConfig()
    clean_cfg._new_namespace('client')
    valid_sections = ['client', 'mysql', 'holland']
    for section in valid_sections:
        if section in config:
            clean_section = client_keys(config[section])
            update_config(clean_cfg.client, clean_section)
    return clean_cfg

def client_keys(config):
    """Create a copy of option_section with non-authentication options
    stripped out.

    Authentication options supported are:
    user, password, host, port, and socket
    """

    clean_namespace = BasicConfig()
    update_config(clean_namespace, config)
    valid_keys = ['user', 'password', 'host', 'port', 'socket']
    for key in config:
        if key not in valid_keys:
            del clean_namespace[key]
        else:
            clean_namespace[key] = unquote(config[key])
    return clean_namespace

def write_options(config, filename):
    quoted_config = INIConfig()
    update_config(quoted_config, config)
    for section in config:
        for key in config[section]:
            if '"' in config[section][key]:
                config[section][key] = quote(config[section][key])

    if isinstance(filename, basestring):
        filename = codecs.open(filename, 'w', 'utf8')
    data = unicode(config)
    print >>filename, data
    filename.close()
