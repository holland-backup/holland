import os
import re
import codecs
from datastructures import SortedDict as OrderedDict

class ConfigError(Exception):
    """General error when processing config"""

class ConfigSyntaxError(ConfigError, SyntaxError):
    """Syntax error when processing config"""

class Config(OrderedDict):
    """Simple ini config"""
    section_cre     = re.compile(r'\s*\[(?P<name>[^]]+)\]\s*(?:#.*)?$')
    key_cre         = re.compile(r'(?P<key>[^:=\s\[][^:=]*)=\s*(?P<value>.*)$')
    value_cre       = re.compile(r"(?:'(?P<sqs>[^'\\]*(?:\\.[^'\\]*)*)'"
                                 r'|"(?P<dqs>[^"\\]*(?:\\.[^"\\]*)*)"'
                                 r'|(?P<raw>.*?))\s*(?:#.*)?$')
    empty_cre       = re.compile(r'\s*($|#|;)')
    cont_cre        = re.compile(r'\s+(?P<value>.+?)$')
    include_cre     = re.compile(r'%include (?P<name>.+?)\s*$')

    #@classmethod
    def parse(cls, iterable):
        """Parse a sequence of lines and return the resulting ``Config`` instance.

        :param iterable: any iterable object that yield lines of text
        :returns: new ``Config`` instance
        """
        cfg = cls()
        section = cfg
        key = None
        for lineno, line in enumerate(iterable):
            if cls.empty_cre.match(line):
                continue
            m = cls.section_cre.match(line)
            if m:
                name = m.group('name')
                #XXX: we throw away cls() if there is an existing
                #     section of the same name (which we will reuse)
                section = cfg.setdefault(name, cls())
                key = None # reset key
                continue
            m = cls.key_cre.match(line)
            if m:
                key, value = m.group('key', 'value')
                key = key.strip()
                value = value.strip()
                section[key] = value
                continue
            m = cls.cont_cre.match(line)
            if m:
                if not key:
                    raise ConfigError("unexpected continuation line")
                else:
                    section[key] += line.strip()
                continue
            m = cls.include_cre.match(line)
            if m:
                path = m.group('name')
                if not os.path.isabs(path):
                    base_path = os.path.dirname(getattr(iterable, 'name', '.'))
                    path = os.path.join(base_path, path)
                subcfg = cls.read([path])
                cfg.merge(subcfg)
                continue
            # XXX: delay to end
            raise ConfigSyntaxError("Invalid line",
                                    (getattr(iterable, 'name', '<unknown>'),
                                     0,
                                     lineno,
                                     line))
        return cfg
    parse = classmethod(parse)

    #@classmethod
    def read(cls, filenames, encoding='utf8'):
        """Read and parse a list of filenames.

        :param filenames: list of filenames to load
        :param encoding: character set encoding of each config file
        :returns: config instance
        """
        main = cls()
        for path in filenames:
            fileobj = codecs.open(path, 'r', encoding=encoding)
            try:
                cfg = cls.parse(fileobj)
            finally:
                fileobj.close()
            main.merge(cfg)
        return main
    read = classmethod(read)

    def merge(self, src_config):
        """Merge another config instance with this one.

        Merging copies all options and subsections from the source config,
        ``src_config``, into this config. Options from ``src_config`` will
        overwrite existing options in this config.

        :param src_config: ``Config`` instance to merge into this instance
        :returns: self
        """
        for key, value in src_config.iteritems():
            if isinstance(value, Config):
                try:
                    section = self[key]
                    if not isinstance(section, Config):
                        # attempting to overwrite a normal key=value with a
                        # section
                        raise TypeError('value-namespace conflict')
                except KeyError:
                    section = self.__class__()
                    self[key] = section
                section.merge(value)
            else:
                self[key] = value

    def meld(self, config):
        """Meld another config instance with this one.

        Merging copies all options and subsections from the source config,
        ``src_config``, into this config. Unlike ``merge()``, existing options
        in this config will always be preserved - ``meld()`` only adds new
        options.

        :param src_config: ``Config`` instance to meld into this instance
        :returns: self
        """
        for key, value in config.iteritems():
            if isinstance(value, Config):
                try:
                    section = self[key]
                    if not isinstance(section, Config):
                        # attempting to overwrite a normal key=value with a
                        # section
                        raise TypeError('value-namespace conflict')
                except KeyError:
                    section = self.__class__()
                    self[key] = section
                section.meld(value)
            else:
                try:
                    self[key]
                except KeyError:
                    # only add the value if it does not already exist
                    self[key] = value

    def write(self, path, encoding='utf8'):
        """Write a representaton of the config to the specified filename.

        The target filename will be written with the requested encoding.
        ``filename`` can either be a path string or any file-like object with
        a ``write(data)`` method.

        :param path: filename or file-like object to serialize this config to
        :param encoding: encoding to writes this config as
        """
        try:
            write = path.write
            write(str(self))
        except AttributeError:
            fileobj = codecs.open(path, 'w', encoding=encoding)
            try:
                fileobj.write(str(self))
            finally:
                fileobj.close()

    def optionxform(self, option):
        """Transforms the option name ``option``

        This method should be overriden in subclasses that want to alter
        the default behavior.

        :param option: option name
        :returns: tranformed option
        """
        return str(option)

    def sectionxform(self, section):
        """Transforms the section name ``section``

        This method should be overriden in subclasses that want to alter
        the default behavior.

        :param section: section name
        :returns: transformed section name
        """
        return str(section)

    def __setitem__(self, key, value):
        if isinstance(value, self.__class__):
            key = self.sectionxform(key)
        elif isinstance(value, basestring):
            key = self.optionxform(key)
        super(Config, self).__setitem__(key, value)

    def __str__(self):
        """Convert this config to a string"""
        lines = []
        for key, value in self.iteritems():
            if isinstance(value, Config):
                lines.append("[%s]" % key)
                lines.append(str(value))
                lines.append("")
            elif isinstance(value, basestring):
                lines.append("%s = %s" % (key, value))
        return os.linesep.join(lines)
