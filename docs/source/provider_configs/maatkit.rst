.. _config-maatkit:

Maatkit Provider Configuration [maatkit]
========================================

Some of these options relate directly to the Maatkit ``mk-parallel-dump``
utility. For more information on these options and the utility itself,
check out the Maatkit ``mk-parallel-dump``
`documentation <http://www.maatkit.org/doc/mk-parallel-dump.html>`_. 
Note that this provider is a proof of concept and should normally not
be used in production.

**lock-method** = flush-lock | lock-tables

    Defines the lock method (``flush-lock`` or ``lock-tables``). 
    
    * flush-lock
    
        Will issue a ``FLUSH TABLES WITH READ LOCK`` prior to the backup. 
        This is basically a global lock which will block writes to the 
        database for the duration of the backup.
    
    * lock-tables
    
        Issues a lock-tables for each database, or for the entire backup
        set.
        
    If this option is not specified, ``flush-lock`` is used.

**biggestfirst** = yes | no

    Backup the biggest tables first.

**binlogpos** = yes | no

    Record the binary log name and position at the time of the backup.

**charset** = [character-set]

    Sets the default character set.

**chunksize** = # [M | G | k]

    Specifies the number of rows or size that each backup file will be.
    Specifying a G, M or k after the number will cause Holland to split
    the chunks by size. Otherwise, it will split by rows.

**ignoreengine** = [engine1, engine2, ..., engineN]

    Skips tables which match any of the provided engines. This can be useful
    in cases where one might not always want to backup certain table-types.
    One example would be tables which use the ARCHIVE engine, since these
    tables may not need to be backed up near as often.

**numthread** = #

    If defined, it will create the provided number of threads for the backup
    operation. If left blank, it will count the number of times 'processor'
    appears in /proc/cpuinfo and use that.

**stopslave** = yes | no

    This is useful only when running Holland on a MySQL slave. Instructs
    Holland to suspend slave services on the server prior to running
    the backup. Suspending the slave does not change the backups, but does
    prevent the slave from spooling up relay logs. The default is not
    to suspend the slave (if applicable).

**flushlog** = yes | no

    If enabled, runs a FLUSH LOGS prior to getting the binary log
    name and position. If left undefined, the default is not to run
    a FLUSH LOGS. Note if using this with setperdb, be aware that 
    FLUSH LOGS can get run quite often, which can cover up error messages
    and create a large number of binary logs needlessly.

**gzip** = yes | no

    Whether or not to compress the backups using gzip. Currently gzip is the
    only option because it is handled by 'mk-parallel-dump' and not by 
    Holland.

**setperdb** = yes | no

    Whether or not to backup each database into its own file.

Database and table filtering
----------------------------

Maatkit's table filtering works slightly different from the other providers
as it uses the same syntax that the `mk-parallel-dump` utility uses.

**databases** = [db1, db2, ..., dbN]

If undefined, will dump all databases.

**ignoredb** = [db1, db2, ..., dbN]

Ignore one or more databases from being backed up.

**dbregex** = [Perl regex]

Regular expression matching on databases using the Perl regular expression
syntax.

**tables** = [table1, table2, ..., tableN]

List specific tables to backup. Note that it is possible to specify
the database and table using dotted notation (database.table).

**tblregex** = [Perl regex]

Regular expression matching on tables using the Perl regular expression
syntax.

**ignoretbl** = [table1, table2, ..., tableN]

A list of tables to exclude from the backup. Like the **tables** option,
use of the database.table syntax is allowed if preferred.


[mysql:client]
--------------
.. toctree::
    :maxdepth: 1

    mysqlconfig
