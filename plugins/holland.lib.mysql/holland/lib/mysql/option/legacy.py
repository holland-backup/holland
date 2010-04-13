"""
Support for parsing and writing my.cnf option
files
"""

import os
import re
import codecs
from types import StringTypes
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import logging

from holland.lib.multidict import MultiDict

LOGGER = logging.getLogger(__name__)

# map sections to lists of params that
# support multiple (repeated) entries
MULTI_KEY = {
    'mysqldump' : [
        'ignore-table',
    ],
    'mysqld' : [
        'replicate-do-db',
        'replicate-do-table',
        'replicate-ignore-db',
        'replicate-ignore-table',
        'replicate-rewrite-db',
        'replicate-wild-do-table',
        'replicate-wild-ignore-table',
    ]
}

class OptionFileParser(object):
    """
    Parser for my.cnf files

    The parse method on this object yields
    OptionFile instances populated with the
    groups and key/value pairs from the underlying
    my.cnf data.
    """


    def __init__(self):
        self.active_group = None

    def parse(self, obj):
        """
        Parse the given object and return an
        OptionFile instance

        If object is a string, this method will
        attempt to open a file of the same name
        and use that for input. Otherwise obj
        should be an iterable that returns lines
        of text representing a text file
        """
        optionobj = OptionFile()
        for line in obj:
            line = line.strip()
            # Skip blank lines
            if not line:
                continue
            # Skip comments
            elif line.startswith('#') or line.startswith(';'):
                continue
            # Groups are of the form [<name>]
            elif line.startswith('['):
                group_name = self._parse_group(line)
                if not group_name:
                    continue
                # Make sure the group exists
                if not group_name in optionobj:
                    optionobj[group_name] = MultiDict()
                # Set it as the active group
                self.active_group = group_name
            # Follow !include or !includedir directives
            elif line.startswith('!include'):
                for optf in self._parse_include(line):
                    optionobj.update(optf)
            # Anything else should be some sort of key[,value] pair
            # where value is optional
            else:
                result = self._parse_option_name(line)
                if not result:
                    continue
                if not self.active_group:
                    continue
                key, value = result
                optionobj[self.active_group].add(key, value)
        return optionobj

    def _parse_group(self, line):
        if not line.endswith(']'):
            return
        group_name = line[1:-1].strip()
        return group_name

    def _parse_include(self, line):
        directive, arg = line.split(None, 1)

        if directive == '!include':
            fileobj = open(arg, 'r')
            yield fileobj
        elif directive == '!includedir':
            if not os.path.isdir(arg):
                return
            for path in os.listdir(arg):
                path = os.path.join(arg, path)
                if not path.endswith('.cnf') and not path.endswith('.ini'):
                    continue
                if not os.path.isfile(path):
                    continue
                fileobj = open(path, 'r')
                yield self.parse(fileobj)

    def _unquote(self, value):
        if len(value) > 1 and value[0] == value[-1] and value[0] in ('"', "'"):
            value = value[1:-1]
        # support weird mysql conversions
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

    def _parse_option_name(self, line):
        if not self.active_group:
            return
        opt_parts = line.split('=', 1)
        # FIXME: Handle inline comments (value may be a quoted string with an embedded '#' in that case)
        if len(opt_parts) == 2:
            key, value = opt_parts
            value = self._unquote(value.strip())
        elif len(opt_parts) == 1:
            key, = opt_parts
            value = True
        key = key.strip().replace('_','-')
        return (key, value)

def canonicalize(optiondict):
    output_dict = MultiDict()
    for section in optiondict:
        if section not in output_dict:
            output_dict[section] = MultiDict()
        for key in optiondict[section]:
            if key in MULTI_KEY.get(section,[]):
                output_dict[section].add(key, optiondict[section][key])
            else:
                output_dict[section][key] = optiondict[section][key]
        output_dict[section].update(optiondict[section])
    return output_dict

class OptionFile(MultiDict):
    def add_section(self, name):
        if not name in self:
            self[name] = MultiDict()
            return True
        return False

    def __str__(self):
        result = StringIO()
        result = codecs.getwriter('utf8')(result)
        output_dict = MultiDict(self)
        for section in self:
            print >>result, "[%s]" % section
            sdict = MultiDict(output_dict.pop(section))
            for key in self[section]:
                if key in MULTI_KEY.get(section,[]):
                    val = sdict.pop(key)
                    print >>result, key,'=',val
                elif key in sdict:
                    value = sdict.getall(key)[-1]
                    del sdict[key]
                    if value is True:
                        print >>result, key
                    else:
                        value = value.replace('"', r'\"')
                        print >>result, key,'=','"%s"' % value
        return result.getvalue()

    def write(self, filename=None):
        if not filename:
            fd, filename = tempfile.mkstemp()
            os.close(fd)
        fileobj = open(filename, 'w')
        print >>fileobj, str(self)
        fileobj.close()
        return filename

def _scrub_cnf(optionfile):
    for key in optionfile:
        if key != 'client':
            LOGGER.debug("Dropping section %s", key)
            del optionfile[key]
    for key in optionfile.get('client', []):
        if key not in ['user','password','host','socket', 'port']:
            LOGGER.debug("Dropping %s from client section", key)
            del optionfile['client'][key]

def make_mycnf(*args, **kwargs):
    """
    Generate a mycnf from the input arguments

    If output is not specified, a temporary file will be created
    and removed on program termination. Each arg should be one of
    a string type, a dictionary or a fileobj.  Each arg will be
    processed in order, with earlier args having their my.cnf
    values overwritten/merged with later args
    """
    base_optionobj = OptionFile()
    parser = OptionFileParser()
    for input in args:
        if isinstance(input, StringTypes):
            try:
                optionobj = parser.parse(open(input, 'r'))
                for key in optionobj:
                    if key in base_optionobj:
                        base_optionobj[key].update(optionobj[key])
                    else:
                        base_optionobj[key] = MultiDict(optionobj[key])
            except IOError, e:
                LOGGER.debug("Failed to parse mysql config %r: %s", input, e)
        else:
            optionobj = parser.parse(input)
            for key in optionobj:
                if key in base_optionobj:
                    base_optionobj[key].update(optionobj[key])
                else:
                    base_optionobj[key] = MultiDict(optionobj[key])

    for key, value in kwargs.items():
        # remove any empty/unset values
        map(value.pop, [opt for opt, val in value.items() if val is None])
        # merge the passed in options - these take precedence
        if key not in base_optionobj:
            base_optionobj.setdefault(key, MultiDict())
        base_optionobj[key].update(value)
    # scrub the final product - we only support connection options and a 'client' section
    _scrub_cnf(base_optionobj)
    return base_optionobj
