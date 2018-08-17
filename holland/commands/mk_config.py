"""
Command support for generating backupset configs
"""

from __future__ import print_function
import os
import sys
import tempfile
import logging
import subprocess

from holland.core.command import Command
from holland.core.plugin import load_first_entrypoint, PluginLoadError
from holland.core.config import HOLLANDCFG
from holland.core.config.checks import VALIDATOR

try:
    from holland.core.config.configobj import ConfigObj, flatten_errors, ParseError
except BaseException:
    from configobj import ConfigObj, flatten_errors, ParseError

LOGGER = logging.getLogger(__name__)


def which(cmd, search_path=None):
    """Find the canonical path for a command"""
    if cmd == '':
        return None

    if not search_path:
        search_path = os.getenv('PATH', '').split(':')

    logging.debug("Using search_path: %r", search_path)
    for name in search_path:
        cmd_path = os.path.join(name, cmd)
        if os.access(cmd_path, os.X_OK):
            return cmd_path

def _find_editor():
    candidates = [
        os.getenv('VISUAL', ''),
        os.getenv('EDITOR', ''),
        '/usr/bin/editor',
        'vim',
        'vi',
        'ed'
    ]
    for command in candidates:
        real_cmd = which(command)
        logging.debug("%r => %r", command, real_cmd)
        if real_cmd:
            return real_cmd

def _report_errors(cfg, errors):
    for entry in flatten_errors(cfg, errors):
        (section,), key, error = entry
        param = '.'.join((section, key))
        if key is not None:
            pass
        else:
            param = ' '.join((section, '[missing section]'))
        if not error:
            error = 'Missing value or section'
        print(param, ' = ', error, file=sys.stderr)

def confirm(prompt=None, resp=False):
    """prompts for yes or no response from the user. Returns True for yes and
    False for no.

    'resp' should be set to the default value assumed by the caller when
    user simply types ENTER.

    >>> confirm(prompt='Create Directory?', resp=True)
    Create Directory? [y]|n:
    True
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y:
    False
    >>> confirm(prompt='Create Directory?', resp=False)
    Create Directory? [n]|y: y
    True

    """

    if prompt is None:
        prompt = 'Confirm'

    if resp:
        prompt = '%s ([%s] or %s): ' % (prompt, 'y', 'n')
    else:
        prompt = '%s ([%s] or %s): ' % (prompt, 'n', 'y')

    while True:
        ans = input(prompt)
        if not ans:
            return resp
        if ans not in ['y', 'Y', 'n', 'N']:
            print('please enter y or n.', file=sys.stderr)
            continue
        if ans == 'y' or ans == 'Y':
            return True
        if ans == 'n' or ans == 'N':
            return False

class MkConfig(Command):
    """${cmd_usage}

    Generate a config file for a backup
    plugin.

    ${cmd_option_list}

    """

    name = 'mk-config'
    aliases = [
        'mc'
    ]

    args = [
        ['--name'],
        ['--edit'],
        ['--provider'],
        ['--file', '-f'],
        ['--minimal', '-m']
    ]
    kargs = [
        {
            'help':'Name of the backupset',
        },
        {
            'help':'Edit the generated config',
            'action':'store_true'
        },
        {
            'help':'Generate a provider config'
        },
        {
            'help':'Save the final config to the specified file',
            'action':'store_true',
            'default':False
        },
        {
            'help':'Do not include comment from a backupplugin\'s configspec'
        }
    ]

    description = 'Generate a config file for a backup plugin'


    # After initial validation:
    #   run through and flag required parameters with a 'REQUIRED' comment
    #   run through and comment out default=None parameters
    @staticmethod
    def _cleanup_config(config, skip_comments=False):
        errors = config.validate(VALIDATOR, preserve_errors=True, copy=True)
        # First flag any required parameters
        for entry in flatten_errors(config, errors):
            section_list, key, error = entry
            section_name, = section_list
            if error is False:
                config[section_name][key] = ''
                config[section_name].comments[key].append('REQUIRED')
            elif error:
                print("Bad configspec generated error", error, file=sys.stderr)

        pending_comments = []
        for section in list(config):
            if pending_comments:
                if skip_comments:
                    comments = []
                else:
                    comments = config.comments.get(section, [])
                comments = pending_comments + comments
                config.comments[section] = comments
                del pending_comments[:]
            for key, value in config[section].items():
                if value is None:
                    if not skip_comments:
                        pending_comments.extend(config[section].comments.get(key, []))
                    pending_comments.append('%s = "" # no default' % key)
                    del config[section][key]
                else:
                    if skip_comments:
                        del config[section].comments[key][:]
                    if pending_comments:
                        if skip_comments:
                            comments = []
                        else:
                            comments = config[section].comments.get(key, [])
                        comments = pending_comments + comments
                        config[section].comments[key] = comments
                        del pending_comments[:]
                    if value is True or value is False:
                        config[section][key] = 'yes' if value else 'no'

        if pending_comments:
            if skip_comments:
                config.final_comment = pending_comments
            else:
                config.final_comment = pending_comments + config.final_comment

        # drop initial whitespace
        config.initial_comment = []
        # insert a blank between [holland:backup] and first section
        try:
            config.comments[config.sections[1]].insert(0, '')
        except IndexError:
            pass

    def run(self, cmd, opts, *plugin_type):
        if not plugin_type:
            print("Missing plugin name", file=sys.stderr)
            return 1
        if opts.name and opts.provider:
            print("Can't specify a name for a global provider config", file=sys.stderr)
            return 1

        try:
            plugin_cls = load_first_entrypoint('holland.backup', plugin_type[0])
        except PluginLoadError as exc:
            logging.info("Failed to load backup plugin %r: %s",
                         plugin_type[0], exc)
            return 1

        try:
            cfgspec = sys.modules[plugin_cls.__module__].CONFIGSPEC
        except BaseException as ex:
            print("Could not load config-spec from plugin %r, %s"
                  % (plugin_type[0], ex), file=sys.stderr)
            return 1

        base_config = """
        [holland:backup]
        plugin                  = ""
        backups-to-keep         = 1
        auto-purge-failures     = yes
        purge-policy            = after-backup
        estimated-size-factor   = 1.0
        """.lstrip().splitlines()
        cfg = ConfigObj(base_config, configspec=cfgspec, list_values=True,
                        stringify=True)
        cfg['holland:backup']['plugin'] = plugin_type[0]
        self._cleanup_config(cfg, skip_comments=opts.minimal)

        if opts.edit:
            done = False
            editor = _find_editor()
            if not editor:
                print("Could not find a valid editor", file=sys.stderr)
                return 1

            tmpfileobj = tempfile.NamedTemporaryFile()
            cfg.filename = tmpfileobj.name
            cfg.write()
            while not done:
                status = subprocess.call([editor, cfg.filename])
                if status != 0:
                    if not confirm("Editor exited with non-zero status[%d]. "
                                   "Would you like to retry?" % status):
                        print("Aborting", file=sys.stderr)
                        return 1
                    else:
                        continue
                try:
                    cfg.reload()
                except ParseError as exc:
                    print("%s : %s" % \
                    (exc.msg, exc.line), file=sys.stderr)
                else:
                    errors = cfg.validate(VALIDATOR, preserve_errors=True)
                    if errors is True:
                        done = True
                        continue
                    else:
                        _report_errors(cfg, errors)

                if not confirm('There were configuration errors. Continue?'):
                    print("Aborting", file=sys.stderr)
                    return 1
            tmpfileobj.close()

        if not opts.name and not opts.file:
            buf = getattr(sys.stdout, 'buffer', sys.stdout)
            cfg.write(buf)
            buf.flush()

        if opts.file:
            print("Saving config to %r" % opts.file, file=sys.stderr)
            filehandle = open(opts.file, 'w')
            buf = getattr(filehandle, 'buffer', filehandle)
            cfg.write(buf)
            buf.flush()
        elif opts.name:
            base_dir = os.path.dirname(HOLLANDCFG.filename)
            path = os.path.join(base_dir, 'backupsets', opts.name + '.conf')
            print("Saving config to %r" % path, file=sys.stderr)
            filehandle = open(path, 'w')
            buf = getattr(filehandle, 'buffer', filehandle)
            cfg.write(buf)
            buf.flush()
        return 0
