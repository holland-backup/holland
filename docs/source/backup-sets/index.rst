Backup-Sets & Providers
=======================

Backup-Sets are the means with which backups are performed in Holland. They
make use of one (sometimes more) providers and plugins to execute a backup
and are configured via a configuration file typically located in the 
Holland backup-sets configuration directory (typically /etc/holland/backupsets).

A backup-set must be called explicitly unless it is in the backupsets list in
the main configuration file (see :ref:`Holland Main Config <holland-main-config>`).

Using a provider in a backup-set configuration is done via specifying the provider
in the ``plugin`` variable in the :ref:`[holland:backup] <backupsetconfigs>`
section. Though optional, the behavior of the plugin can be modified by 
adding one or more sections in named brackets (ie ``[mysqldump]``) within the 
backup-set configuration file and specifying various options for the provider.
See :ref:`config` for more information about how Holland configuration files work 
in general.

Many plugins come with an example configuration file located in the ``examples``
directory under the Holland backup-set directory (by default, 
``/etc/holland/backupsets``)

As of Holland 1.1, the following plugins are currently available in the main
Holland distribution. 3rd party plugins are possible, but are not documented here.

  * :ref:`mysqldump`
  * :ref:`mysql-lvm`
  * :ref:`mysqldump-lvm`
  * :ref:`Xtrabackup`
  * :ref:`pgdump`
  * :ref:`sqlite`
  * :ref:`random` 

