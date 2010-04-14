===========
pylvmbackup
===========

---------------------------------------------
create fast database backups from LVM volumes
---------------------------------------------

:Author: andrew.garner@rackspace.com
:Date:   2009-07-26
:Copyright: Rackspace Proprietary
:Version: 0.3
:Manual section: 1
:Manual group: backup utilities


SYNOPSIS
========

  pylvmbackup [options] backup-directory

DESCRIPTION
===========

pylvmbackup snapshots an existing LVM volume and backs up the data on
the snapshot.  Mechanisms are in place to flush MySQL data prior to
the snapshot process and unlock immediately after, as well as running
transactional recovery on the snapshot data directory.

pylvmbackup is inspired by mylvmbackup, providing the following additional
benefits:

1. All options are optional.  The target lvm mount is determined by the
   MySQL data directory.  This is found by using a pre-existing ~/.my.cnf
   to connect to the local server and requesting the server ``datadir``
   variable.
2. Fully modular approach internally. A message bus architecture signals
   various subscribers at each stage of the LVM snapshot lifecycle. MySQL
   specific behavior is only a "plugin" and can be removed or replaced
   (e.g. by Postgres specific paths) without affecting any other code.
3. Paranoia about removing snapshots at all costs
4. Less convoluted options
5. No dependencies other than the lvm2 toolchain and python2.3+

pylvmbackup currently lacks the following features of mylvmbackup:

1. No syslog support yet.
2. Only tar based backups are currently supported.
3. No snapshot only backups.

OPTIONS
=======

-?, --help              Show help.
-c config-file, --config=config-file
Use the specified config file (default: /etc/pylvmbackup.conf)

LVM Options
-----------
--logical-volume=lvname
                        The name for the logical volume to be backed up.
                        (default: autodetect)
--snapshot-name=snapshot
                        The name for the new logical volume snapshot.
                        (default: target volume + _snapshot)
--snapshot-size=size
                        Gives  the  size to allocate for the new logical
                        volume. (default: the smaller of 20% of --logical-
                        volume size or the free space on the underlying volume
                        group)
--mount-directory=mount-directory
                        Where to mount the snapshot (default: /mnt/snapshot)

MySQL Connection Options
------------------------
    These options configure how pylvmbackup connects to MySQL in order to
    perform any necessary flush or administrative actions.

--defaults-file=option-file
                        MySQL .cnf file to use (default: ~/.my.cnf)
-u user, --user=user
                        MySQL User (default: root)
-p, --password          Prompt for MySQL password. Note: This option takes no
                        argument. Setting a password on the command line is
                        bad practice - use a --defaults-file instead.
                        (default: False)
-h host, --host=host
                        Host of MySQL Server. (default: localhost)
-S socket-file, --socket=socket-file
                        Socket file of MySQL server. (default: none)
-P port, --port=port
                        MySQL port number. (default: 3306)
--skip-extra-flush-tables
                        Don't Run an extra FLUSH TABLES before acquiring a
                        global read lock with FLUSH TABLES WITH READ LOCK
                        (default: False)
--skip-flush-tables 
                        Don't flush tables or acquire a read-lock.(default:
                        False)
--innodb-recovery       Run a MySQL bootstrap process against the LV snapshot
                        to initiate InnoDB recovery prior to making the
                        backup. (default: True)

PROBLEMS
========

1. Config file not yet implemented.
2. EINTR handling could be improved.
3. More intelligent backup management.

SEE ALSO
========

* ``mylvmbackup <http://www.lenzg.net/mylvmbackup>``
* ``holland <http://hollandbackup.org>``

BUGS
====

* Postgres not supported

