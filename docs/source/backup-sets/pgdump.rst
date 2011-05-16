.. _pgdump:

pgdump
======

The pgdump provider is a front-end to the PostgreSQL pgdump utility and can
backup databases into logical (SQL) and binary-based backups.

Configuration
-------------

[pgdump]
********

**format** = plain | tar | custom

    Specify the format of the backup. See PostgreSQL documentation on 
    pgdump for more inforamtion.

    * plain

        Perform a logical (SQL) backup

    * tar

        Create a tar archive suitable for input into pg_restore. This format
        allows for reordering and/or exclusion of database objects at time of
        restore.

    * custom

        Create a custom archive suitable for intput into pg_restore. This
        is the default if no option is specified.

**role** = string

    Sets the role after establishing a connection to PostgreSQL but before
    the begin begins. The default is not to set a role.

**additional-options** = string

    Pass any additional options to pgdump.

[pgauth]
********

**username** = username or None

    Specify a user to connect to PostgreSQL with. If omitted, system default
    is used.

**password** = password or None
    
    Specify a password (clear-text) to connect to PostgreSQL with. If 
    omitted, system default is used.

**hostname** = hostname or None

    Specify a hostname or IP address to connect to PostgreSQL with. If 
    omitted, system default is used.

**port** = # or None

    Specify a port number to connect to PostgreSQL with. If 
    omitted, system default is used.

.. include:: compression.rst

Note that some ``[pgdump]`` options supersede compression, such as when using
the custom backup format.
