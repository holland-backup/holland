.. _mysql-lvm:

mysql-lvm
=========

mysql-lvm uses LVM snapshots to create safe binary-based backups of MySQL with
minimal locking involved. In many cases, mysql-lvm offers supperior performance 
to  :ref:`mysqldmp` but with less configurability. If logical backups are 
required, consider using the :ref:`mysqldump-lvm` provider to get the best of
both worlds.

Note that MySQL must be running on an LVM volume with sufficient free space
for snapshots. Also note that while this provider only requires short locks
in most cases, there is a write-penalty caused by the copy-on-write nature
of LVM snapshots. In InnoDB-centric solutions, :ref:`xtrabackup` may be a
worth alternative to reduce the write penalty incurred while performing
a backup.

[mysql-lvm]
***********

**snapshot-size** = <size-in-MB>

    The size of the snapshot itself. By default it is 20% of the size of  the 
    MySQL LVM mount or the remaining free-space in the Volume Group (if there 
    is less than 20% available) up to 15GB. If snapshot-size is defined, the 
    number represents the size of the snapshot in megabytes.

**snapshot-name** = <name>

    The name of the snapshot, the default being the name of the MySQL LVM 
    volume + "_snapshot" (ie Storage-MySQL_snapshot)
    
**snapshot-mountpoint** = <path>    
    
    Where to mount the snapshot. By default a randomly generated directory 
    under /tmp is used.

**innodb-recovery** = yes | no

    Whether or not to run an InnoDB recovery operation. This avoids needing 
    to do so during a restore, though will make the backup process itself 
    take longer. The default is to skip recovery.

**lock-tables** = yes | no
    
    Whether or not to run a FLUSH TABLES WITH READ LOCK to grab various
    bits of information (such as the binary log name and position). Disabling
    this requires that binary logging is disabled and InnoDB is being used
    exclusively. Otherwise, it is possible that the backup could contain
    crashed tables. The default is to lock tables.
    
**extra-flush-tables** = yes | no
    
    Whether or not to run a FLUSH TABLES before running the full 
    FLUSH TABLES WITH READ LOCK. Should make the FLUSH TABLES WITH READ LOCK
    operation a bit faster. The default is run run a FLUSH TABLES.

[tar]
*****

**exclude** = list

    A list of exclusions from the resulting tarball backup. If undefined, 
    ``mysql.sock`` will be excluded.

.. include:: mysqld.rst

.. include:: mysqlclient.rst

.. include:: compression.rst

