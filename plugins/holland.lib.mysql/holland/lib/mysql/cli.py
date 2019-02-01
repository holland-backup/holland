# mycmdparser.py
# Utility class to parse info from various mysql cli tools
# Written by: Andrew Garner <andrew.garner@rackspace.com>

"""
This module includes utilities to parse mysql
command line utilities such as mysql, mysqlcheck,
mysqld (server), etc.

Accepted options are available as dictionary attributes
on the mysqlcliParser.
Further attributes:
- Returns tuple (major, minor, rev) for cli utility
cli_version()
- Returns list of my.cnf locations this cli utility searches
  by default
mycnf_locations()
- Returns list of config groups within each my.cnf this utility
  reads by default
mycnf_groups()
"""
import re
from future import standard_library

standard_library.install_aliases()
from subprocess import getstatusoutput  # pylint: disable=C0413,C0411


class CmdOption(object):
    """
    Create CmdOption class
    """

    def __init__(self, **kwargs):
        self.short_option = kwargs.get("short_option", None)
        self.long_option = kwargs.get("long_option", None)
        self.default_value = kwargs.get("default_value", None)
        self.arg_type = kwargs.get("arg_type", None)
        self.arg_optional = kwargs.get("arg_optional", True)

    def __str__(self):
        arg_type = ("=%-7s") % (self.arg_type) if self.arg_type else (" ") * (8)
        return "--%-30s%s [%s]" % (self.long_option, arg_type, self.default_value)


class MyCmdParser(dict):
    """
    Parse the --help --verbose output of a MySQL command and generate a
    dictionary of accepted short and long options.
    """

    def __init__(self, cli_path):
        dict.__init__(self)
        self.cli_path = cli_path
        self.cli_info = self._run_cli_help()
        self.cli_version = self._parse_cli_version()
        self.mycnf_locations = self._parse_mycnf_locations()
        self.mycnf_groups = self._parse_mycnf_groups()
        self.cli_options = self._parse_cli_options()
        self.cli_defaults = self._parse_cli_defaults()
        for opt in self.cli_options:
            sopt, lopt, arg, optional = opt
            lopt = lopt.replace("_", "-")
            if arg is not None:
                default_value = self.cli_defaults.get(lopt)
            else:
                arg = None
                default_value = None
            opt = CmdOption(
                short_option=sopt,
                long_option=lopt,
                default_value=default_value,
                arg_optional=optional,
                arg_type=arg,
            )
            self[sopt] = opt
            self[lopt] = opt

        self.cli_options = list(self.values())

    def _run_cli_help(self):
        args = [
            self.cli_path,
            "--no-defaults",
            "--loose-user=nobody",
            "--help",
            "--verbose",
        ]
        cli_cmd = " ".join(args)
        status, cli_output = getstatusoutput(cli_cmd)

        if status != 0:
            raise IOError(cli_output)

        return cli_output

    def _parse_cli_options(self):
        # Find all valid options
        optcre = re.compile(
            r"^  (?:-(?P<short_option>.), )?"
            + r"--(?P<opt>[-a-zA-Z0-9_]+)"
            + r"(?:(?:=(?P<type>#|name))|"
            + r"(?:\[=(?P<opt_type>#|name)\]))?",
            re.M,
        )
        valid_options = optcre.findall(self.cli_info)
        return valid_options

    @staticmethod
    def _parse_cli_default_value(value):
        if re.match(r"^\d+$", value):
            return int(value)
        if value == "TRUE":
            return True
        if value == "FALSE":
            return False
        if value == "(No default value)":
            return None
        return value

    def _parse_cli_defaults(self):
        defaults = {}
        defaults_section_cre = re.compile(r"\n(?:-+? -+?\n(.*))(\n|$)", re.M | re.S)
        match = defaults_section_cre.search(self.cli_info)
        if match:
            defaults_cre = re.compile(r"^(?P<opt>[a-zA-Z_\-]+)(?:\s+(?P<value>.+?))?$")
            for line in match.groups()[0].splitlines():
                match1 = defaults_cre.match(line)
                if match1:
                    key, value = match1.groups()
                    key = key.replace("_", "-")
                    value = self._parse_cli_default_value(value)
                    defaults[key] = value
        return defaults

    def _parse_cli_version(self):
        vers_cre = re.compile(r"^.* Ver .*?(\d+\.\d+.\d+)", re.M)
        match = vers_cre.search(self.cli_info)
        if match:
            return tuple(map(int, match.groups()[0].split(".")))
        return None

    def _parse_mycnf_locations(self):
        # Default options are read from the following files in the given order:
        # /etc/my.cnf ~/.my.cnf
        mycnf_loc_cre = re.compile(r"Default options.*order:\n([^\n]+)", re.M)
        match = mycnf_loc_cre.search(self.cli_info)
        if match:
            mycnf_locs = match.groups()[0].split()
            return mycnf_locs
        return None

    def _parse_mycnf_groups(self):
        # The following groups are read: mysql_cluster cli server cli-5.0
        mycnf_grp_cre = re.compile(r"^The.*groups are read: (.+)$", re.M)
        match = mycnf_grp_cre.search(self.cli_info)
        if match:
            return match.groups()[0].split()
        return None
