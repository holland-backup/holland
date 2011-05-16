.. _mysqldump-lvm:

mysqldump-lvm
=============

One of the issues with running a standard ``mysqldump`` is that it can 
cause some potentially expensieve table-locking in order to produce a
consistent backup. The mysqldump-lvm provider overcomes this by taking
an LVM snapshto of the MySQL datadir and bootstrapping an instance of 
MySQL on-top of it, thereby avoiding costly locks on the live database.

This obviously requires that MySQL is running on an LVM volume that 
has available free space for snapshotting. Though locking is largely
avoided (save for a quick lock to mount the snapshot), there is a
non-trivial write-performance penalty due to the copy-on-write nature
of LVM.

To use this plugin, set the ``plugin`` variable the 
:ref:`[holland:backup] <backupsetconfigs>` section of the backup-set
configuration file to ``mysqldump-lvm``. 

Configuration
-------------

[mysqldump]
***********

Same options as the [mysqldump] section of the :ref:`mysqldump` plugin,
though some settings such as ``lock-method`` are less relevant.

[mysqldump-lvm]
***************

Same options as the [mysqldump-lvm] section of the :ref:`mysql-lvm` plugin
with the exception of ``innodb-recoveriy`` since that is performend when
the additional instance of MySQL is started (it cannot be disabled).

.. include:: mysqld.rst

.. include:: compression.rst

