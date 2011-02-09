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
by a mix of providers and backup-sets.

Backup-Sets
^^^^^^^^^^^

Each backup-set implements exactly one provider and will inherit the default
values of that provider. These values can be overridden to adjust the
behavior of the backup set. This includes defining what databases or tables
to include (or exclude) in the backup, the type of compression used (if 
any), what locking method to use, among other things.

Providers
^^^^^^^^^

Providers essentially provide a backup service for use in a backup set. 
As of Holland 0.5, there are 5 providers:

* mysqldump

    Uses the ``mysqldump`` utility to backup databases.

* Example

    This is used solely as a template for designing providers. It otherwise
    does nothing.

* MySQL + LVM

    Backup MySQL databases using LVM snapshots which allows for near lockless 
    or fully lockless (when transactional engines are used) backups.
    
There are also plans to eventually implement the following providers:    
    
* MySQL Cluster

    MySQL Cluster already offers a simple way of producing lockless backups,
    however these methods do not often include table-creation data,
    routines, etc. In addition, backups from the Cluster are stored on 
    each of the Data Nodes.
    
    Therefore, this provider would facilitate backing up and aggregating
    the Cluster backups into one centralized location, as well as backing
    up the periphery data necessary should a full restore be necessary.

As Holland is a framework, it can actually backup most anything as long
as there is a provider for it. This includes things that have nothing to do 
with databases. The idea is to present an easy to use and clear method
of backing up and restoring backups no matter the source.
