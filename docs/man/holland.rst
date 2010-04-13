=========
 holland
=========

---------------------------------------------
pluggable database backup agent
---------------------------------------------

:Author: Andrew Garner <andrew.garner@rackspace.com>
:Date:   2009-04-09
:Copyright: Other/Proprietary
:Version: 0.1
:Manual section: 1
:Manual group: text processing

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
* maatkit (mk-parallel-dump)

Command plugins are used to add additional commands to the holland shell.
Currently available commands include:

* backup        - run one or more backup jobs
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

1. holland is still an alpha-quality product and is not recommended for production use.
2. operational windows are not yet supported
3. restore is still a manual process

SEE ALSO
========

* `Python Eggs <http://peak.telecommunity.com/DevCenter/PythonEggs>`
* `pkg_resources <http://peak.telecommunity.com/DevCenter/PkgResources>`
* `Plugins Using Eggs <http://ianbicking.org/docs/pycon2006/plugins.html>`

BUGS
====

* mk-config is new and has various formatting issues  
* purge is run at the end of every backup.  If a backup is interrupted, 
  purge will be delayed until the end of the next successful backup run.
* disk-space estimations are still quite rough and may overestimate in many cases.
  As a workaround, most plugins provide a scale factor setting to adjust estimates 
  accordingly.

