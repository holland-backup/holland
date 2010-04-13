.. _config-mysqlhotcopy:

MySQL Hot Copy Provider Configuration [mysqlhotcopy]
====================================================

Reminder: This provider is really only for MyISAM tables. It does NOT
handle transactional tables (such as InnoDB). 

**mysql-binpath** = /path/to/mysql/bin

    Defines the location of the MySQL binary utilities. If not provided,
    Holland will use whatever is in the path.

**lock-method** = lock-tables | flush-lock

    Defines the lock method (``flush-lock`` or ``lock-tables``). 
    
    * flush-lock
    
        Will issue a ``FLUSH TABLES WITH READ LOCK`` prior to the backup. 
        This is basically a global lock which will block writes to the 
        database for the duration of the backup.
    
    * lock-tables
    
        Issues a lock-tables for each database, or for the entire backup
        set.
    
    If this option is not specified, ``lock-tables`` is used.

**partial-indexes** = yes | no

    If set to true, Holland will only backup the first 2k of a .MYI file, 
    which can save quite a bit of space. This requires repairing the tables
    to rebuild the remainder of the index on a restore, however.

**archive-method** = dir | zip | tar

    Which method to use when archiving the files. 
    ``dir`` creates a standard directory
    ``zip`` creates a ZIP file
    ``tar`` creates a tar.gz file

**stop-slave** = yes | no
    Whether to stop the slave before commencing with the backup

**bin-log-position** = yes | no
    Whether to record the binary log name and position at the time of the
    backup.

Database and Table filtering
----------------------------
.. toctree::
    :maxdepth: 1

    databasefiltering

[mysql:client]
--------------
.. toctree::
    :maxdepth: 1

    mysqlconfig
