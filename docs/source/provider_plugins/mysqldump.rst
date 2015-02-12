.. _config-mysqldump:

mysqldump Provider Configuration [mysqldump]
============================================

Backs up one or more MySQL databases using the mysqldump tool.

[mysqldump]
-----------

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

**exclude-invalid-views** =  yes | no (default: no)

    Whether to automate exclusion of invalid views that would otherwise cause
    mysqldump to fail.  This adds additional overhead so this option is not
    enabled by default.

    When enabled, thos option will scan the INFORMATION_SCHEMA.VIEWS table and
    execute SHOW FIELDS against each view.  If a view is detects as invalid, an
    ignore-table option will be added to exclude the table.  Additionally, the
    plugin will attempt to save the view definion to 'invalid_views.sql' in the
    backupset's backup directory.

    .. versionadded:: 1.0.8

**dump-routines** = yes | no (default: yes)

    Whether or not to backup routines in the backup set directly. Routines
    are stored in the 'mysql' database, but it can sometimes be convenient
    to include them in a backup-set directly.

    .. versionchanged:: 1.0.8
       This option now enabled by default.

**dump-events** = yes | no

    Whether or not to dump events explicitly. Like routines, events are
    stored in the 'mysql' database. Nonetheless, it can sometimes be
    convenient to include them in the backup-set directly.

    **Note**: This feature requires MySQL 5.1 or later. The mysqldump plugin
    will automatically disable events if the version of mysqldump is too old.

    .. versionchanged:: 1.0.8
       This option is now enabled by default


**stop-slave** = yes | no

    Stops the SQL_THREAD during the backup. This means that writes
    from the master will continue to spool but will not be replayed.
    This helps avoid lock wait timeouts among things while still
    allowing data to be spooled from the master.

    Note that previous versions of Holland prior to 1.0.6 simply
    ran a STOP SLAVE instead, which suspends both replication
    threads.

    Holland will log some fairly useful information to the 'backup.conf'
    file in regards to log files and positions::

      [mysql:replication]
      slave_master_log_pos = 147655593
      slave_master_log_file = db2-bin.007120
      master_log_file = mysqld-bin.000001
      master_log_pos = 313

    The ``slave_master_*`` values refer to the file and position that the slave
    has replicated to from its master server (often useful when cloning slaves,
    for instance).

    The ``master_log_*`` values refer to the binary log and position
    **of the slave** itself and is only logged is binary logging on the slave
    is enabled. This information can be used to setup chained replication
    as well as point in time recovery of that slave (which would be useful
    if one is only doing backups on the slave and not the master).

**bin-log-position** = yes | no

    Record the binary log name and position at the time of the backup as a
    SQL comment in backup SQL file itself. This directly correlates to the
    ``--master-data=2`` 'mysqldump' command-line option.

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

    When backing up all databases within a single file, the backup file
    will be named ``all_databases.sql``. If compression is used, the 
    compression extension will be appended to the filename
    (e.g. ``all_databases.sql.gz``).

**additional-options** = <mysqldump argument>[, <mysqldump argument>]

    Can optionally specify additional options directly to ``mysqldump`` if
    there is no native Holland option available.  This option accepts a comma
    delimited list of arguments to pass on the commandline.

**extra-defaults** = yes | no (default: no)

    This option controls whether mysqldump will only read options as set by
    holland or if additional options from global config files are read.  By
    default, the plugin only uses optons as set in the backupset config and
    includes authentication credentials only from the [client] section in
    ~/.my.cnf.

**estimate-method** = plugin | const:<size> (default: plugin)

    This option will skip some of the heavyweight queries necessary to
    calculate the size of tables to be backed up.  If a constant size is
    specified, then only table names are evaluated and only if table filtering
    is being used. Additionally, engines will be looked up via SHOW CREATE
    TABLE if lock-method = auto-detect, in order for the plugin to determine if
    tables are using a transactional storage engine.  With 'plugin', the
    default behavior of reading both size information and table names from the
    information schema is used, which may be slow particularly for a large
    number of tables.

Database and Table filtering
----------------------------
.. toctree::
    :maxdepth: 1

    databasefiltering

.. include:: compression.rst

.. include:: mysqlconfig.rst
