Developing Holland Plugins
==========================

Holland provides ways to extend the base functionality by providing plugins.
Many common plugins are included in the base holland distributions but
additional plugins can come from 3rd party sources as well.

This guide will discuss how Holland uses plugins and how to write useful
plugins for the holland system.

Understanding Entry Points
--------------------------

Holland uses setuptools entrypoints to locate and load potential plugins. Entry
points are a simple way for a Python package to advertise python objects.

For instance, the 'holland-mysqldump' package advertises that it provides a 
'mysqldump' plugin for the 'holland.backup' group. This is done in a standard
setup.py.

plugins/holland.backup.mysqldump/setup.py::

    from setuptools import setup, find_packages
    
    version = '1.1.0'
    
    setup(
        # standard setup.py attributes
        ...
        entry_points="""
        [holland.backup]
        mysqldump = holland.backup.mysqldump:provider
    )

The 'mysqldump' entrypoint here points to the actual physical location of the
module, ``holland.backup.mysqldump`` and notes that this module will have the
attribute ``provider``.  When a user requests to load the ``mysqldump`` backup
plugin then Holland effectively does ``load('holland.backup', 'mysqldump')``
which will look through advertised ``[holland.backup]`` entrypoints and find
one with the name ``mysqldump``.

Holland supports multiple entry point groups including ``[holland.backup]``
backup plugins:

* [holland.backup] - backup plugins
* [holland.commands] - additional commands for the cli interface
* [holland.stream] - additional output formats (used for compression,
                     encryption and other tranformations by backup 
                     plugins)
* [holland.hooks] - Callback 'hook' plugins for holland


Backup Plugins
--------------

The most common plugin type in holland is the backup plugin.  This provides the
machinery for actually running a backup.  Holland provides a path where backup files
should be stored and the configuration for the plugin as requested by the user and it
is the plugin's job to actually generate useful backup files.

A basic Backup Plugin
~~~~~~~~~~~~~~~~~~~~~

All backup plugins in holland are python classes.  Here is an example of a
minimal backup plugin::

    import logging
    from holland.core import BackupPlugin

    class MyFirstBackupPlugin(BackupPlugin):
        def backup(self):
            logging.info("This is where my backup code would go")
    
        def plugin_info(self):
            return dict(
                name='my-backup-plugin',
                author='Me <i@myself.example.com>',
                summary='A simple backup plugin example',
                description='''
                A longer description describing my plugin and briefly how and
                why it should be used.
                ''',
                version='1.0', # the version of this plugin
                api_version='1.1', # the version of holland this plugin is written for
            )

A backup plugin essentially has two required methods to do anything useful:

 1. A ``backup()`` method.  This starts a backup - copying files or running some series of commands
 2. A ``plugin_info()`` method.  This provides some basic information about your plugin including
    the canonicall ``name``, the ``author`` of the plugin, a one line ``summary``, a multi-line
    ``description``, a basic ``version`` string and the ``api_version`` your plugin was written again.

The above plugin is very basic and doesn't generate any files, so isn't very useful.  Since we inherit from
the ``holland.core.BackupPlugin`` class holland provides a basic ``path`` variable that gives a backup plugin
a directory where Holland would like the plugin to store its backup files.

Here is a more complex example::

    import os
    import logging
    from holland.core import BackupPlugin

    class MyFirstBackupPlugin(BackupPlugin):
        def backup(self):
            backup_directory = self.path
            my_first_backup_file = os.path.join(backup_directory, 'backup_data.txt')
            open(my_first_backup_file, 'w').write("My Backup Data")
            logging.info("Saved some backup data to %s", my_first_backup_file)
    
        def plugin_info(self):
            return dict(
                name='my-backup-plugin',
                author='Me <i@myself.example.com>',
                summary='A simple backup plugin example',
                description='''
                A longer description describing my plugin and briefly how and
                why it should be used.
                ''',
                version='1.0', # the version of this plugin
                api_version='1.1', # the version of holland this plugin is written for
            )

Backup data should be saved relative to the backup directory provided by
holland.  This is the ``self.path`` variable setup by the base ``BackupPlugin`` 
class.  This will be a directory like ``/var/spool/holland/my-backupset/$date/``
and os.path can be used to generate paths under that directory.

A backup plugin can save whatever data it would like under that directory.

Plugin Configuration
~~~~~~~~~~~~~~~~~~~~

A Backup plugin can accept configuration parameters to specify what should
be backed up or how to connect to a database.

Acceptable parameters are provided by a plugin via a ``configspec``.  This is
an ini-like config that details what parameters are valid and what sort of values
those parameters should take.  Holland will automatically validate a user's config
against this specification and give useful errors or warnings if the config is
invalid in some way.

Specifying the Configspec
+++++++++++++++++++++++++

To specify a configspec in your backup plugin a ``configspec()`` method should
be implemented::

    import os
    import logging
    from holland.core import BackupPlugin, Configspec

    class MyFirstBackupPlugin(BackupPlugin):
        def estimate(self):
            return 42

        def backup(self):
            backup_directory = self.path
            my_first_backup_file = os.path.join(backup_directory, 'backup_data.txt')
            open(my_first_backup_file, 'w').write("My Backup Data")
            logging.info("Saved some backup data to %s", my_first_backup_file)
    
        def configspec(self):
            return Configspec.from_string("""
            [my-backup-plugin]
            directory-to-backup = string
            backup-everything   = boolean(default=yes)
            """)

        def plugin_info(self):
            return dict(
                name='my-backup-plugin',
                author='Me <i@myself.example.com>',
                summary='A simple backup plugin example',
                description='''
                A longer description describing my plugin and briefly how and
                why it should be used.
                ''',
                version='1.0', # the version of this plugin
                api_version='1.1', # the version of holland this plugin is written for
            )

Looking specifically at just the ``configspec()`` method::


        def configspec(self):
            return Configspec.from_string("""
            [my-backup-plugin]
            directory-to-backup = string
            backup-everything   = boolean(default=yes)
            """)

This notes that a backupset .conf file should have a ``[my-backup-plugin]`` section.
This should provide a ``directory-to-backup`` string and optionally may specify a
``backup-everything`` boolean flag that should be true or false.  If ``backup-everything``
is not specified then this will default to 'yes' (or True).

To see how Holland interprets this it's useful to look at the Config API briefly::

  >>> from holland.core import Config, Configspec
  >>> spec = Configspec.from_string("""
  ... [my-backup-plugin]
  ... directory-to-backup = string
  ... backup-everything   = boolean(default=yes)
  ... """)
  >>> cfg = Config.from_string("""
  ... [my-backup-plugin]
  ... directory-to-backup = /var/lib/mysql
  ... backup-everything = False
  ... """)
  >>> cfg
  Config({'my-backup-plugin': Config({'directory-to-backup': '/var/lib/mysql', 'backup-everything': 'False'})})
  >>> cfg['my-backup-plugin']['backup-everything']
  'False'
  >>> spec
  Configspec({'my-backup-plugin': Configspec({'directory-to-backup': 'string', 'backup-everything': 'boolean(default=yes)'})})
  >>> validated_cfg = spec.validate(cfg)
  >>> validated_cfg
  Config({'my-backup-plugin': Config({'directory-to-backup': '/var/lib/mysql', 'backup-everything': False})})
  >>> validated_cfg['my-backup-plugin']['backup-everything']
  False

Here a configspec is defined as in the previous example.  This accepts a string
and a boolean flag.  ``cfg`` is how holland would load a user .conf from
/etc/holland/backupsets/<backupset>.conf.  When ``cfg`` is loaded we see all the values
are strings::

  >>> cfg['my-backup-plugin']['backup-everything']
  'False'

However, once the config is validated Holland converts these to the right
datatype - as specified in the configspec::

  >>> validated_cfg['my-backup-plugin']['backup-everything']
  False

So our plugin does not need to do a lot of jumping through hoops when testing
the ``backup-everything`` flag.  The plugin can do something as simple as::

        def backup(self):
            if self.config['my-backup-plugin']['backup-everything']:
                # copy self.config['my-backup-plugin']['director-to-backup']
                # to self.backup_directory (our current backup destination)

Configspec checks
+++++++++++++++++

In the last example the configspec used both strings and boolean values for a
flag.  Holland's config implementation supports a wide variety of checks that
can be used:

  * boolean()
  * integer([min=value][, max=value])
  * float()
  * list() - a comma seperated list of values
  * tuple() - like list() - a comma separate list of values - but validates as a tuple
  * option([option1][,option2...]) - a string value that must be one choice in a series of options
  * cmdline() - a shell command line - parsed through python's shlex to provide a list of argument values
  * log_level() - a python logging log level - when validated this converts a string log level name to
                  an integer log level (e.g. 'info' => logging.INFO)
 
Estimating the backup size
~~~~~~~~~~~~~~~~~~~~~~~~~~

Holland will perform a space estimate before starting a backup.  This is used
to ensure at least some minimal amount of space is available in the directory
Holland is writing before a backup begins. Holland 1.1 can calculate this from
several sources defined in the backupset .conf under ``[holland:backup]``:

  * The size of a directory (``estimation-method = dir:/var/lib/mysql/``)
  * A constant size specified by a user (``estimation-method = const:4.5G``)
  * The output of a command (``estimation-method = cmd:du -sh /var/lib/mysql/ | cut -f1``)
  * Asking a BackupPlugin how large it thinks a backup will be

The default behavior is to ask a plugin for its estimate.  Plugins have a lot of domain
specific knowledge and will probably be more accurate than other methods.

To provide an estimate in your backup plugin you just need to implement a ``estimate()`` method::

    import os
    import logging
    from holland.core import BackupPlugin

    class MyFirstBackupPlugin(BackupPlugin):
        def estimate(self):
            return 42

        def backup(self):
            backup_directory = self.path
            my_first_backup_file = os.path.join(backup_directory, 'backup_data.txt')
            open(my_first_backup_file, 'w').write("My Backup Data")
            logging.info("Saved some backup data to %s", my_first_backup_file)
    
        def plugin_info(self):
            return dict(
                name='my-backup-plugin',
                author='Me <i@myself.example.com>',
                summary='A simple backup plugin example',
                description='''
                A longer description describing my plugin and briefly how and
                why it should be used.
                ''',
                version='1.0', # the version of this plugin
                api_version='1.1', # the version of holland this plugin is written for
            )

In this example, the backup plugin will always return a constant '42 bytes' as
its estimate.  For a real plugin, database metadata or a file listing would be
used with the plugin filtering out things the user doesn't want to back up (as
specified in its config).

Pre and Post methods
~~~~~~~~~~~~~~~~~~~~

A backup plugin can also provide ``pre()`` and ``post()`` methods.  ``pre()``
will be called after ``configure()`` but before ``estimate()``.  This is useful
to do any setup that might be shared by the ``estimate()`` and ``backup()`` methods.
For instance, in mysqldump we may connect to the MySQL server to get a list of databases
in ``pre()`` and have ``estimate()`` and ``backup()`` reuse those results.

``post()`` is called after ``backup()`` has completed.  Holland's backup API will call
``post()`` regarldess of success or failure and give the plugin to do any final cleanup
for the backup run.

Hook Plugins
------------

Hook plugins are new in Holland 1.1 and provide a way to perform actions at
various points during a backup and add fine-grained funtionality to the
backup process.

There are essentially four events that a hook may be defined at:

  * setup-backup - before a plugin is configured or a backup-store set.  This
                   event can be useful to tweaking a plugins config before the
                   plugin actually configures itself.  For instance, the mysqldump
                   backup plugin has an example hook implementation that can be
                   used to dynamically choose an available MySQL server from a
                   list of slaves.  This uses a hook to rewrite the ``[mysql:client]``
                   section in a mysqldump .conf configuration.
  * before-backup - before ``plugin.backup()`` is run. This can be useful to do any
                    last minute adjustments.  In some environments iptables rules
                    may be set to drop a slave of out of load balanced pool or
                    a notification sent off that a backup is about to begin.
  * after-backup  - after a backup has completed successfully.  This may be
                    used to copy backups to another server for disaster-recovery
                    or staging processes.  Notification could be sent at this point
                    to notify that a backup has finished.
  * backup-failure - after a backup has failed.  This event is useful for notifying
                     that a failure has occurred and requires administrative investigation.

Hooks must register themselves with a particular event.  This is done through a simple
method that the Holland will call on the a hook class


A basic hook plugin
~~~~~~~~~~~~~~~~~~~

A hook plugin is a python class that derives from ``holland.core.hook.HookPlugin``.
This is a ``holland.core.plugin.ConfigurablePlugin``.  A simple hook plugin
looks like:

.. code-block:: python
   :linenos:

    import logging
    from holland.core import BaseHook
    
    class MyHook(BaseHook):
        def execute(self, **kwargs):
            logging.info("My hook is being run")
    
    
        def register(self, signal_group):
            signal_group.after_backup.connect(self, weak=False)

``signal_group`` is a simple interface to the various events holland supports.  A plugin should
register itself with the events it wants to listen to.  In some cases a hook implementation will
always be associated with some event.  In other cases allowing the events to be configurable by
a user will be useful.

Making a hook configurable
~~~~~~~~~~~~~~~~~~~~~~~~~~

A hook is made configurable similar to a ``BackupPlugin``. A ``configspec()`` method should
be added. However no ``[section]`` should be defined - hooks may only specify attributes,
but not sections. This is because holland validates user-defined sectons against multiple
potential user sections.

.. code-block:: python
   :linenos:

    import logging
    from holland.core import BaseHook
    
    class MyHook(BaseHook):
        def execute(self, **kwargs):
            logging.info("My hook is being run")
    
    
        def register(self, signal_group):
            for event in self.config['events']:
                signal_group[event].connect(self, weak=False)
     
        def configspec(self):
            return Configspec.from_string("""
            events = option('before-backup', 'after-backup', default='before-backup')
            """)

How hooks are defined
~~~~~~~~~~~~~~~~~~~~~

::

    [holland:backup]
    plugin = mysqldump
    hooks = first-do-this, second-do-that

    [first-do-this]
    plugin = my-hook-plugin
    events = before-backup

    [second-do-that]
    plugin = my-hook-plugin
    events = after-backup


