Usage and Implementation Overview
=================================

Holland is built around the concept of plugins, though for the end user, most
of these plugins will be in the form of backup providers and their helper
plugins. These are configured by way of a backup-set which defines the
characteristics of a particular backup.

Backup-Sets
^^^^^^^^^^^
A backup-set is compromised of global, provider, and helper plugin
configuration options which make up a particular backup. For instance, once
might want to backup a handful of MySQL databases using some specific
mysqldump settings; while backing up another set of MySQL databases using
different settings. To do this, one might create two backups sets for each
scenario.

Most plugins come with a set of defaults such that only values that need to be
overridden need to be specified in a backup-set if desired. Such defaults
can be modified on a global basis by editing the global provider configuration
files (see below).

Provider Plugins
^^^^^^^^^^^^^^^^

Provider plugins provide a backup service for use in a backup set. They
are the interface between Holland and the method of backing up data.
As of Holland |version|, there are 5 providers included with Holland:

* mysqldump

    Uses the ``mysqldump`` utility to backup MySQL databases.

* MySQL + LVM

    Backup MySQL databases using LVM snapshots which allows for near lockless
    or fully lockless (when transactional engines are used) backups. MySQL
    must be running on an LVM volume with sufficient free extents to store
    a working snapshot. It is also extremely ill-advised to store the backup
    on the same volume as MySQL.

* Support for `Percona XtraBackup <http://www.percona.com/software/percona-xtrabackup>`_

    .. versionadded:: 1.0.8

    Backup MySQL databases using `Percona XtraBackup <http://www.percona.com/software/percona-xtrabackup>`_.
    This provides a near lockless backup when using the InnoDB storage engine
    while also providing a mysqlhotcopy style backup for MyISAM tables.

* pgdump

    Backup PostgreSQL databases using the ``pgdump`` utility.

* Example

    This is used solely as a template for designing providers. It otherwise
    does nothing.

As Holland is a framework, it can actually backup most anything as long
as there is a provider plugin for it. This includes things that have
nothing to do with databases. The idea is to present an easy to use
and clear method of backing up and restoring backups no matter the source.
