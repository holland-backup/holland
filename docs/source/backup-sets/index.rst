Holland Backup-Sets
===================

Backup-Sets are the means with which backups are performed in Holland. They
make use of one (sometimes more) providers and plugins to execute a backup
and are configured via a configuration file typically located in the 
Holland backup-sets configuration directory (typically /etc/holland/backupsets).

A backup-set must be called explicitly unless it is in the backupsets list in
the main configuration file (see :ref:`Holland Main Config <holland-main-config>`).

Providers
---------

As of Holland 1.1, the following plugins are currently available in the main
Holland distribution. 3rd party plugins are possible, but are not documented here.

Using a provider in a backup-set configuration is done via specifying the provider
in the ``plugin`` variable in the :ref:`[holland:backup] <backupsetconfigs>`
section. Though optional, the behavior of the plugin can be modified by 
adding a section in named brackets (ie ``[mysqldump]``) within the backup-set 
configuration file and specifying various options for the provider. Some i
providers have multiple bracketed sections, typically when they extend the
functionality of another provider (such as the ``mysqldump-lvm`` provider). See
:ref:`config` for more information about how Holland configuration files work in 
general.

Many plugins come with an example configuration file located in the ``examples``
directory under the Holland backup-set directory (by default, 
``/etc/holland/backupsets``)

  * :ref:`mysqldump`
  * :ref:`mysqldump-lvm`
  * :ref:`mysql-lvm`
  * :ref:`Xtrabackup`
  * :ref:`sqlite`
  * :ref:`pgdump`
  * :ref:`random`

Compression
-----------

Compression is configured within a ``[compression]`` sub-section.

**method** = gzip | pigz | bzip | lzop | lzma

    Define which compression method to use. Note that ``lzop`` and
    ``lzma`` may not be available on every system and may need to be compiled
    / installed.

**inline** = yes | no

    Whether or not to pipe the output of mysqldump into the compression
    utility. Enabling this is recommended since it usually only marginally
    impacts performance, particularly when using a lower compression
    level.

**level** = 0-9

    Specify the compression ratio. The lower the number, the lower the
    compression ratio, but the faster the backup will take. Generally,
    setting the lever to 1 or 2 results in favorable compression of
    textual data and is noticeably faster than the higher levels.
    Setting the level to 0 effectively disables compression.

**bin-path** = <full path to utility>

    This only needs to be defined if the compression utility is not in the
    usual places or not in the system path.

