Holland Config Files
====================

By default, Holland's configuration files reside in /etc/holland. The main
configuration file is holland.conf and there is a configuration file for
each backup.

Config File Syntax
------------------

Holland uses ini-like files very similar to MySQL's .cnf format. These consist
of five basic syntax elements

* comments.  Comments in a config file always start with '#' and go to the end
  of a line.
* blank lines. 
* sections.  Sections are contained within square brackets and group options 
  together.
* options.  Options are in key = value format.  A value may span multiple lines.
* include directives.  As of Holland 1.1.0 the config file format supports
  %include directives in a config file in order to include other config files

Multi-line values
+++++++++++++++++

Holland 1.1 supports option values that span multiple lines. Each additional
line must start with one-or-more spaces and the value will be considered a 
continuation of the original option.

A quick multi-line example::

  [mysqldump]
  databases = test,
              dev,
              staging,
              other

This is most commonly used for very long option values - for instance the
mysqldump plugins accepts lists of patterns to include or exclude and in
some cases these can get longer than will neatly fit on a standard 
80-character line.

Include directives
++++++++++++++++++

Include directives allow neatly merging multiple configurations together.
A include directive starts with %include followed by a path.

A quick include example::

  [mysqldump]
  %include /etc/holland/staging-exclusion.conf

staging-exclusions.conf::

  [mysqldump]
  exclude-databases = production*,
                      testing*,
                      mysql*

  exclude-tables = *.log

Examples
++++++++

Here is a more thorough example that demonstrates all of the features of a
Holland 1.1 config file.

daily-backups.conf::

  # This is the basic backup configuration that is the same across all backup
  # plugins
  [holland:backup]
  plugin = mysqldump  # this notes which backup plugin should be used

  # The mysqldump plugin looks for options in a [mysqldump] section
  [mysqldump]
  databases = foo, bar, baz
  file-per-database = yes

  # include a global authentication file - this is shared among multiple
  # mysql plugins
  %include /etc/holland/mysql-global-auth.conf


mysql-global-auth.conf::

  [mysql:client]
  user = holland-backup
  password = holland-backup-password
  socket = /tmp/custom_socket_location.sock


holland.conf - main config
--------------------------

The main configuration file (usually /etc/holland/holland.conf) defines
both global settings as well as the active backup sets. It is divided into
two sections :ref:`[holland]<holland-config>` and :ref:`[logging]<logging-config>`. 

.. _holland-config:

[holland]
+++++++++

.. describe:: plugin-dirs

    Defines where the plugins can be found. This can be a comma-separated 
    list but usually does not need to be modified.
    
.. _holland-config-backup-directory:    
    
.. describe:: backup-directory

    Top-level directory where backups are held. 
    
.. _holland-config-backupsets:

.. describe:: backupsets

    A comma-separated list of all the backup sets Holland should backup.
    Each backup set is defined in ``/etc/holland/backupsets/<name>.conf`` by
    default.
    
.. describe:: umask

    Sets the umask of the resulting backup files.
    
.. describe:: path (optional)

    Defines a command search path for processes spawned by holland

.. describe:: tmpdir (optional)

    Sets the temporary directory used by holland and its plugin when
    generating temporary files.

    If tmpdir is unset then this will be set the first directory the user
    can create files in from the following list:

    1. The directory named by the TMPDIR environment variable.
    2. The directory named by the TEMP environment variable.
    3. The directory named by the TMP environment variable.
    4. A platform-specific location:
       On Windows, the directories C:\TEMP, C:\TMP, \TEMP, and \TMP, in that order.
       On all other platforms, the directories /tmp, /var/tmp, and /usr/tmp, in that order.
       As a last resort, the current working directory.

.. _logging-config:
    
[logging]
+++++++++

.. describe:: filename

    The log file holland should write all logging messages to.

.. describe:: level

    Sets the verbosity of Holland's logging process. Available options are
    ``debug``, ``info``, ``warning``, ``error``, and ``critical``

Provider Configs
----------------

These files allow configuring the defaults for all backup configurations that
use a particular plugin.  This was useful before Holland 1.1's %include
directive to manage global settings for multiple backup configs that use the
same plugin - for instance daily and weekly mysqldump backups.

Holland will load the main backup configuration and will merge this configuration
with the providers/$plugin.conf if it exists.  By default holland looks for the
providers directory within the same directory as the holland.conf.  So for a
standard install of Holland there will be /etc/holland/holland.conf and the
global providers config files will be under /etc/holland/providers/.

This functionality is largely deprecated as of Holland 1.1 and it is recommended
that you use %include functionality to achieve the same effect in a more flexible
way.

Backup-Set Configs
------------------

Backup-Set configuration files largely inherit the configuration options of
the specified provider. To define a provider for the backup set, you must
put the following at the top of the backup set configuration file::

    [holland:backup]
    plugin = <plugin>
    backups-to-keep = #
    estimated-size-factor = #
    
**plugin** = <plugin>

    This is the name of the provider that will be used for the backup-set.
    This is required in order for the backup-set to function.

**backups-to-keep** = #

    Specifies the number of backups to keep for a backup-set.
    
**estimated-size-factor** = #

    Specifies the scale factor when Holland decides if there is enough
    free space to perform a backup.  The default is 1.0 and this number
    is multiplied against what each individual plugin reports its 
    estimated backup size when Holland is verifying sufficient free
    space for the backupset.

Backup-Set files are defined in the "backupsets" directory which is,
by default, ``/etc/holland/backupsets``. The name of the backup-set is 
defined by its configuration filename and can really be most anything. That
means backup-sets can be organized in any arbitrary way, although backup
set files must end in .conf. The file extension is not part of the name of
the backup-set.

As noted above, in order for a backup-set to be active, it must be listed in
the :ref:`backupsets<holland-config-backupsets>` variable.

Backups are placed under the directory defined in the 
:ref:`backup_directory<holland-config-backup-directory>`
section of the main configuration file. Each backup resides under a directory
corresponding to the backup-set name followed by a date-encoded directory.
