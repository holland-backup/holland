.. _config-mysql-lvm:

MySQL LVM Provider Configuration [mysql-lvm]
============================================

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
    take longer.

**lock-tables** = yes | no
    
    Whether or not to run a FLUSH TABLES WITH READ LOCK to grab various
    bits of information (such as the binary log name and position). Disabling
    this requires that binary logging is disabled and InnoDB is being used
    exclusively. Otherwise, it is possible that the backup could contain
    crashed tables.
    
**extra-flush-tables** = yes | no
    
    Whether or not to run a FLUSH TABLES before running the full 
    FLUSH TABLES WITH READ LOCK. Should make the FLUSH TABLES WITH READ LOCK
    operation a bit faster.

[compression]
-------------
.. toctree::
    :maxdepth: 1

    compression

[mysql:client]
--------------
.. toctree::
    :maxdepth: 1

    mysqlconfig
