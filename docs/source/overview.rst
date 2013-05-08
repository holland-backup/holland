Usage and Implementation Overview
=================================

Because Holland is very pluggable, it may first seem a bit confusing when
it comes to configuring Holland to do something useful. Out of the box,
Holland is designed to backup MySQL databases using the mysqldump provider.
This is the simplest setup, and may be sufficient for most people. However, 
others may wish to have more fine-grained control over their backups and/or 
use another method other than mysqldump.

For instance, one can configure a backup set to backup certain databases
using mysqldump, others using the mysql-lvm plugins etc. All this is done
by a mix of plugins (sometimes called providers) and backup-sets.

Backup-Sets
^^^^^^^^^^^

Each backup-set implements a backup plugin (provider) and often some helper
plugins for things such as compression. Plugins come with a set of defaults
such that only values that need to be overridden need to be specified, 
although it is perfectly acceptable to specify options that are already 
default - one would merely be stating the obvious. Doing so woudl also 
make sure future changes to the defaults in Holland do not impact existing
backup-sets.

Provider Plugins
^^^^^^^^^^^^^^^^

Provider plugins provide a backup service for use in a backup set. The 
are the interface between Holland and the method of backing up data.
As of Holland 1.0.8, there are 5 providers included with Holland:

* mysqldump

    Uses the ``mysqldump`` utility to backup MySQL databases.

* MySQL + LVM

    Backup MySQL databases using LVM snapshots which allows for near lockless 
    or fully lockless (when transactional engines are used) backups. MySQL
    must be running on an LVM volume with sufficient free extents to store
    a working snapshot. It is also extremely ill-advised to store the backup
    on the same volume as MySQL.

* XtraBackup

    .. versionadded:: 1.0.8
    
    Backup MySQL databases using Percona's 
    `XtraBackup <http://www.percona.com/software/percona-xtrabackup>`_ tool.
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
