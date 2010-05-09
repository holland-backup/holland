.. _config-mysqldump:

mysqldump Provider Configuration [mysqldump]
============================================

**mysql-binpath** = /path/to/mysql/bin

    Defines the location of the MySQL binary utilities. If not provided,
    Holland will use whatever is in the path.
    
**lock-method** = flush-lock | lock-tables | single-transaction | auto-detect | none

    Defines which lock method to use. By default, auto-detect will be used.
    
    * flush-lock
    
        flush-lock will place a global lock on all tables involved in the backup
        regardless of whether or not they are in the backup-set. If 
        file-per-database is enabled, then flush-lock will lock all tables 
        for every database being backed up. In other words, this option may not
        make much sense when using file-per-database.
    
    * lock-tables
    
        lock-tables will lock all tables involved in the backup. If
        file-per-database is enabled, then lock-tables will only lock all the
        tables associated with that database.
    
    * single-transaction
    
        Forces the use of ``--single-transaction`` which enabled
        semi-transparent backups of transactional tables. Forcing this
        can cause inconsistencies with non-transactional tables, however. 
        While non-transactional tables will still lock, they will only 
        lock when they are actually being backed up. **Use this setting
        with extreme caution when backing non-transactional tables.**
    
    * auto-detect
    
        Let Holland decide which option to use by checking to see if
        a database or backup-set only contains transactional tables. If 
        so, ``--single-transaction`` will be used. Otherwise,
        ``--lock-tables`` will be used.
    
    * none
    
        Does absolutely no explicit locking when backing up the
        databases or backup-set. This should only be used when backing
        up a slave and only after the slave has been turned off 
        (ie, this can be used with the **stop-slave** option).
    
**dump-routines** = yes | no

    Whether or not to backup routines in the backup set directly. Routines
    are stored in the 'mysql' database, but it can sometimes be convenient
    to include them in a backup-set directly.
    
**dump-events** = yes | no

    Whether or not to dump events explicitly. Like routines, events are 
    stored in the 'mysql' database. Nonetheless, it can sometimes be 
    convenient to include them in the backup-set directly. 
    
    **Note**: This feature requires MySQL 5.1 or later.
    
**stop-slave** = yes | no

    This is useful only when running Holland on a MySQL slave. Instructs
    Holland to suspend slave services on the server prior to running
    the backup. Suspending the slave does not change the backups, but does
    prevent the slave from spooling up relay logs. The default is not
    to suspend the slave (if applicable).

**bin-log-position** = yes | no

    Record the binary log name and position at the time of the backup.
    
    Note that if both 'stop-slave' and 'bin-log-position' are enabled, 
    Holland will grab the master binary log name and position at the time 
    of the backup which can be useful in using the backup to create slaves 
    or for point in time recovery using the master's binary log. This 
    information is found within the 'backup.conf' file located in the
    backup-set destination directory 
    (/var/spool/holland/<backup-set>/<backup> by default). For example::
    
      [mysql:replication]
      slave_master_log_pos = 4512
      slave_master_log_file = 260792-mmm-agent1-bin-log.000001
    
**flush-logs** = yes | no
    
    Whether or not to run FLUSH LOGS in MySQL with the backup. When FLUSH
    LOGS is actually executed depends on which if database filtering is being
    used and whether or not file-per-database is enabled. Generally speaking,
    it does not make sense to use flush-logs with file-per-database since the 
    binary logs will not be consistent with the backup.
    
**file-per-database** = yes | no

    Whether or not to split up each database into its own file. Note that
    it can be more consistent an efficient to backup all databases into
    one file, however this means that restore a single database can
    be difficult if multiple databases are defined in the backup set.
    
**additional-options** = <mysqldump arguments>

    Can optionally specify additional options directly to ``mysqldump`` if
    there is no native Holland option for it.

Database and Table filtering
----------------------------
.. toctree::
    :maxdepth: 1

    databasefiltering


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
