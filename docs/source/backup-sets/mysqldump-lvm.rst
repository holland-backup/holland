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
configuration file to ``mysqldump-lvm``. If desired, a ``[mysqldump]``
section can be defined with all the same features of the :ref:`mysqldump`
provider (though some settings are no longer totally relevant). A
``[mysqldump-lvm]`` section can also be defined whose options are identical
to the :ref:`mysql-lvm` plugin with the exception of ``innodb-recovery`` since
this happens when the additional instance of MySQL is started.

Finally, a ``[mysqld]`` section can be defined to configure the bootstrapped
instance with various settings which are as follows:

**mysqld-exe** = path

    Path to the MySQL binary. By default, ``mysqld`` or ``/usr/libexec/mysqld``
    is used.

**user** = user

    User to run the MySQL bootstrapped instance as. By default ``mysql`` is used.

**innodb-buffer-pool-size** = #M

    The size to set the innodb buffer pool of the bootstrapped instance.
    The default is 128M. If there is additional RAM available on the server, 
    setting this higher will improve the total backup time. Be mindful not to 
    set this too high to avoid starving the system of RAM.

**key-buffer-size** = #M

    The size to set the key buffer of the bootstrapped instance. The default
    is 8M. Setting this higher can improve backup performance (though less 
    significantly than the ``innodb-buffer-pool-size``. Be mindful not to
    set this too high to avoid straving the system of RAM.
    
**tmpdir** = path

    The location to use for the tmpdir of the bootstrapped instance, with
    the default being the default for MySQL.
