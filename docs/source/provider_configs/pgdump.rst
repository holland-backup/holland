.. _config-pgdump:

pgdump Provider Configuration [pgdump]
======================================

Backs up a PostgreSQL instance using the pgdump utility.

[pgdump]
--------

**format** = custom | tar | plain (default: custom)

    Defines the --format option for pg_dump.  This defaults to --format=custom.
    The custom format is required for pg_restore to do partial restore as well
    as enabling parallel restores.

**additional-options** = <command-string>

    Pass additional options to the pg_dump command

.. include:: compression.rst

[pgauth]
--------

**username** = <name>

    Username for pg_dump to authenticate with

**password** = <string>

    Password for pg_dump to authenticate with

**hostname** = <string>

    Hostname for pg_dump to connect with

**port** = <integer>

    TCP port for pg_dump to connect on
