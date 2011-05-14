Holland Backup-Sets
===================

Backup-Sets are the means with which backups are performed in Holland. They
make use of one (sometimes more) providers and plugins to execute a backup
and are configured via a configuration file typically located in the 
Holland backup-sets configuration directory (typically /etc/holland/backupsets).

A backup-set must be called explicitly unless it is in the backupsets list in
the main configuration file (see :ref:`Holland Main Config <holland-main-config>`).

Providers
---------

As of Holland 1.1, the following plugins are currently available in the main
Holland distribution. 3rd party plugins are possible, but are not documented here.

  * :ref:`mysqldump`
  * :ref:`mysqldump-lvm`
  * :ref:`mysql-lvm`
  * :ref:`Xtrabackup`
  * :ref:`sqlite`
  * :ref:`pgdump`
  * :ref:`random`

.. _mysqldump:

mysqldump
*********

mysqldump 

.. _mysqldump-lvm:

mysqldump-lvm
*************

mysqldump-lvm

.. _mysql-lvm:

mysql-lvm
*********

mysql-lvm

.. _Xtrabackup:

Xtrabackup
**********

XtraBackup

.. _sqlite:

sqlite
******

sqlite

.. _pgdump:

pgdump
******

pgdump

.. _random:

random
******
