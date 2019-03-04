"""MySQL option file support"""

import os
import re
import glob
import codecs


def expandpath(path):
    """Expand a path to an absolute path

    This will convert a relative path to an absolute path and also expand any
    user directories such as ~/ to the user's homedir.
    """
    return os.path.abspath(os.path.expanduser(path))


def remove_inline_comment(value):
    """Remove a MySQL inline comment from an option file line"""
    escaped = False
    quote = None
    for idx, char in enumerate(value):
        if char in ('"', "'") and not escaped:
            if not quote:
                quote = char
            elif quote == char:
                quote = None
        if not quote and char == "#":
            return value[0:idx]
        escaped = quote and char == "\\" and not escaped
    return value


def unquote_option_value(value):
    """Remove quotes from a string."""
    if len(value) > 1 and value[0] in ('"', "'") and value[0] == value[-1]:
        return value[1:-1]
    return value


def unescape_option_value(value):
    """Unescape an option value per MySQL supported escape sequences

    See: http://dev.mysql.com/doc/refman/5.0/en/option-files.html
    """
    meta_mapping = {"b": "\b", "t": "\t", "n": "\n", "r": "\r", "\\": "\\", "s": " ", '"': '"'}

    return re.sub(r'\\(["btnr\\s])', lambda m: meta_mapping[m.group(1)], value)


def unpack_option_value(value):
    """Process an option value according to MySQL's syntax rules"""
    value = remove_inline_comment(value)
    value = value.strip()
    value = unquote_option_value(value)
    value = unescape_option_value(value)
    return value


def resolve_option(item):
    """Expand an option prefix to the full name of the option"""
    known = ["host", "password", "port", "socket", "user"]
    candidates = [key for key in known if key.startswith(item)]

    if len(candidates) > 1:
        # mimic MySQL's error message
        raise ParseError("ambiguous option '%s' (%s)" % (item, ",".join(candidates)))
    if not candidates:
        return item

    return candidates[0]


def find_includes(include_directive):
    """Find includes for the given !include* directive"""
    directive, path = include_directive.split(None, 1)
    if directive == "!includedir":
        return glob.glob(os.path.join(path, "*.cnf")) + glob.glob(os.path.join(path, "*.ini"))
    if directive == "!include":
        return path
    raise ParseError("Invalid include directive %s" % include_directive)


class ParseError(Exception):
    "Exception raised when parsing an option file"


class OptionFile(dict):
    """Represent a MySQL option file"""

    KV_CRE = re.compile(r"(?P<key>[^=\s]+?)\s*(?:=\s*(?P<value>.*))?$")

    def read_options(self, iterable):
        """Parse lines from the data source specified by ``iterable``
        """
        section = None

        path = getattr(iterable, "name", "<unknown>")

        for lineno, line in enumerate(iterable):
            line = line.strip()
            if line.startswith("!include"):
                paths = find_includes(line)
                self.process_includes(paths)
            elif not line:
                continue
            elif line.startswith("#") or line.startswith(";"):
                continue
            elif line.startswith("["):
                section = remove_inline_comment(line).strip()
                if section.startswith("[") and section.endswith("]"):
                    section = section[1:-1].lower()
                    self.setdefault(section, dict())
                else:
                    raise ParseError(
                        "Wrong group definition in config file: "
                        "%s at line %d" % (path, lineno + 1)
                    )
            else:
                key_value = self.parse_key_value(line)
                if key_value:
                    key, value = key_value
                    self[section][key] = value
                else:
                    raise ParseError(line, "%s:%s" % (path, lineno + 1))

    def read(self, filenames):
        """Read and parse a list of option file paths

        :returns: list of paths successfully processed
        """
        processed = []
        for path in filenames:
            try:
                fileobj = codecs.open(expandpath(path), "r", encoding="utf8")
            except IOError:
                continue
            try:
                self.read_options(fileobj)
                processed.append(path)
            finally:
                fileobj.close()
        return processed

    def parse_key_value(self, line):
        """Process a key/value directive according to MySQL syntax rules

        :returns: tuple if line is a valid key/value pair otherwise returns None
                  If this is a bare option such as 'no-auto-rehash' the value
                  element of the key/value tuple will be None
        """
        match = self.KV_CRE.match(line)
        if match:
            key, value = match.group("key", "value")
            if value:
                value = unpack_option_value(value)
            else:
                key = remove_inline_comment(key)
            key = resolve_option(key)
            return key, value
        return None

    def process_includes(self, paths):
        """Call ``read_options()`` for every valid file in paths

        :returns: list of invalid paths that were skipped
        """
        skipped = []
        for path in paths:
            try:
                fileobj = codecs.open(expandpath(path), "r", encoding="utf8")
            except IOError:
                skipped.append(path)
                continue
            try:
                # python2.3 does not support try/except/finally
                try:
                    self.read_options(fileobj)
                except IOError:
                    continue
            finally:
                fileobj.close()
        return skipped
