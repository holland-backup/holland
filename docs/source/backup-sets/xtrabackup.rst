.. _xtrabackup:

XtraBackup
==========

Xtrabackup is a front-end to the Percona XtraBackup utility and is best
suited for backing up InnoDB-centric MySQL databases in a raw backup
similar to :ref:`mysql-lvm`. Typically, XtraBackup offers superior
performance over LVM due to a smaller penalty taken on writes and
does not require that MySQL reside on an LVM volume.

XtraBackup must be installed before this plugin will work properly.

Configuration
-------------

[xtrabackup]
************

**global-defaults** = path

    The location of a defaults file (such as a my.cnf) to use with XtraBackup.
    The default is to is ``/etc/my.cnf``.

**innobackupex** = path

    The location of the innobackupex utility. By default, 
    ``innobackupex-1.5.1`` is used (thus assuming that the utility is in the
    system path.

**slave-info** = yes | no

    Whether or not to provide replication information within the resulting
    backup. The default is not to write out slave information.

**no-lock** = yes | no

    Whether or not to perform any locking. Locking is normally done to backup
    any MyISAM tables, .frm files and other miscellaneous files. BE CAREFUL
    when disabling this as it can cause inconsistent backups! If in doubt,
    set this to yes (which is also the default).

.. include:: compression.rst

