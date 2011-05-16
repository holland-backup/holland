.. _sqlite:

sqlite
======

sqlite is a plugin which uses the internal .dump functionality built into
SQLite and produces a logical (SQL) dump.

Configuration
-------------

[sqlite]
********

**databases** = list

    Specify of list of databases to explicitly backup.

**binary** = path

    Location of the sqlite binary (defaults to ``/usr/bin/sqlite3``)

.. include:: compression.rst
