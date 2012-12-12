=========
 holland
=========

---------------------------------------------
pluggable database backup agent
---------------------------------------------

:Author: Andrew Garner <andrew.garner@rackspace.com>
:Date:   2009-05-08
:Copyright: Other/Proprietary
:Version: 0.9.9
:Manual section: 1
:Manual group: Holland Backup Framework

.. TODO: authors and author with name <email>

SYNOPSIS
========

holland [global-options] command [command-options]

DESCRIPTION
===========

Holland provides a pluggable framework through which to perform 
database backups.

This framework primarily targets MySQL, but there are plans to
support other database platforms such as PostgreSQL in the future

Holland supports three kinds of plugins currently:

* Backup plugins
* Command plugins
* Library plugins

Backup plugins are used for defined backup jobs in order to perform some
task. The currently available backup plugins include:

* mysqldump
* mysqlhotcopy (raw file backups for non-transactional tables)
* mysql-lvm (raw file backups using LVM filesystem snasphots)
* mysqldump-lvm (mysqldump backups using LVM filesystem snapshots)
* pgdump

Command plugins are used to add additional commands to the holland shell.
Currently available commands include:

* backup        - run one or more backup jobs
* purge         - purge one or more old backups
* list-plugins  - show known plugins
* list-backups  - show completed backup jobs
* mk-config     - generate a job config for a given backup plugin

Library plugins simply provide support for other plugins. 
Currently available library plugins include:

* holland.lib.mysql         - Core MySQL support
* holland.lib.archive       - Standardized access to multiple archive formats
* holland.lib.compression   - Standardized access to compression streams

OPTIONS
=======

--config=<file>         Read configuration settings from <file>, if it exists.
--version, -V           Show this program's version number and exit.
--help, -h              Show this help message and exit.

PROBLEMS
========

1. restore is still a manual process

SEE ALSO
========

* ``man holland-mysqlhotcopy``
* ``man holland-mysqldump``
* ``man holland-mysqllvm``
* ``man holland-mysqldump-lvm``
* ``man holland-pgdump``
