.. _config:


Holland Config Files
====================

By default, Holland's configuration files reside in /etc/holland. The main
configuration file is holland.conf, however there are a number of other 
configuration files for configuring default settings for providers and for
configuring backup sets.

Each configuration file has one ore more sections, defined by square
brackets Underneath each section, one or more configuration option
can be specified. These options are in a standard "option = value" format.
Comments are prefixed by the # sign.

Note that many settings have default values and, as a result, can either
be commented out or omitted entirely.

holland.conf - main config
--------------------------

The main configuration file (usually /etc/holland/holland.conf) defines
both global settings as well as the active backup sets. It is divided into
two sections :ref:`[holland]<holland-config>` and :ref:`[logging]<logging-config>`. 

.. _holland-config:

[holland]
^^^^^^^^^

.. describe:: plugin-dirs

    Defines where the plugins can be found. This can be a comma-separated 
    list but usually does not need to be modified.
    
.. _holland-config-backup_directory:    
    
.. describe:: backup_directory

    Top-level directory where backups are held. 
    
.. _holland-config-backupsets:

.. describe:: backupsets

    A comma-separated list of all the backup sets Holland should backup.
    Each backup set is defined in ``/etc/holland/backupsets/<name>.conf`` by
    default.
    
.. describe:: umask

    Sets the umask of the resulting backup files.
    
.. describe:: path

    Defines a path for holland and its spawned processes

.. _logging-config:
    
[logging]
^^^^^^^^^

.. describe:: filename

    The log file itself.

.. describe:: level

    Sets the verbosity of Holland's logging process. Available options are
    ``debug``, ``info``, ``warning``, ``error``, and ``critical``

Provider Configs
----------------

These files control the global settings / defaults for the providers used by 
the backup-sets. Many of these global settings can be overridden if defined
in a backup-set. Note that each provider's configuration file should begin
with ``[provider-name]``.

.. toctree::
    :maxdepth: 2

    provider_configs/example
    provider_configs/mysqldump
    provider_configs/mysqlhotcopy
    provider_configs/maatkit
    provider_configs/mysql-lvm

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
:ref:`backup_directory<holland-config-backup_directory>`
section of the main configuration file. Each backup resides under a directory
corresponding to the backup-set name followed by a date-encoded directory.







