Generating MySQL Cluster Backups
================================

MySQL Cluster backups are a complex beast.  A ``START BACKUP`` directive is
sent to a management node which instructs each of the data nodes to dump backup
files to their respective BackupDataDir.  To restore you will need to collect
those backup files in order to reapply them to the data nodes.

The Delphini backup plugin attemps to make this process much easier with
holland.  A backup directive is issued to a management node and once that
succeeds delphini will ssh into each of the data nodes and retrieve the backup
files to a centralized location.

.. _holland-config:

Holland Backupset Configuration
===============================

Holland uses standard ini-like config files in .conf files - one for each
backup configuration.  A sample config file for delphini might look like this:

::
  [holland:backup]
  plugin = delphini # this can also be 'mysql-cluster'

  [mysql-cluster]
  connect-string 	= 127.0.0.1
  default-ssh-user 	= mysql
  default-ssh-keyfile	= /etc/holland/holland.key

  [compression]
  method		= gzip
  level			= 6

``[holland:backup]`` is a standard section that defines config values common in
all backup config files.  The only required piece of information here is what
plugin you want to use - for delphini this will be called ``delphini`` but is
also aliased to ``mysql-cluster``.  Additional parameters may be specified here
to adjust how holland purges old and failed backups when running backups with
this configuration.  For more information see:
`hollandbackup.org <http://hollandbackup.org>`_

``[mysql-cluster]`` is the main section for delphini with the parameters needed
to connect to the cluster and its data nodes.  Currently only three parameters
are supported:

  * ``connect-string`` to be able to connect to a management node and issue a
    backup directive.  This defaults to localhost so if backups are run on the
    management server no further configuration is necessary.
  * ``default-ssh-user`` to specify what user to use when connecting to the
    data node servers. This defaults to 'root', but another user is strongly
    recommended.
  * ``default-ssh-keyfile`` to specify an ssh key to use for authentication to
    the data node servers.  This must be specified in order to successfully
    authenticate with a remote server.  See :ref:`generating-ssh-keys`

``[compression]`` is a standard configuration section for using holland's
configurable compression support.  Holland 1.0 currently supports several
compression methods:

  * gzip and pigz (parallel gzip)
  * bzip2
  * lzop
  * lzma/xz

Further the compression level can be set to 0 or the compression method set to
``none`` to completely disable compression.


.. _generating-ssh-keys:

Generating SSH Keys
===================

Generally you will use the ssh-keygen command to generate an SSH key on linux.

This will generate both a public and private key.  The public key (e.g.
id_rsa.pub) should be copied to each data node and put in the 
``default-ssh-user``'s ``~/.ssh/authorized_keys`` file.  The private key (e.g.
id_rsa) should be copied to some location readable by the holland process.

::

  $ ssh-keygen -t rsa
  $ scp ~/.ssh/id_rsa.pub each.data_node1.server:.ssh/authorized_keys2
  $ sudo cp -a ~/.ssh/id_rsa /etc/holland/holland.key

Required Permissions
====================

To copy files on each data node the ``default-ssh-user`` will need read access
to the node's ``BackupDataDir``.  This will usually be the same as ``DataDir``
unless this has been changed.  I like to use /var/lib/mysql-cluster/ as mysql
cluster's ``DataDir`` and backups will be saved under
/var/lib/mysql-cluster/BACKUPS/.

If you want Delphini to also purge backups once they have been copied off the
server the ``default-ssh-user`` will also need access to delete files under the
``BackupDataDir``.  If ndbd is started as the system root user then this will
mean that ``default-ssh-user`` will also need to be root.

Example Setup and Execution
===========================

This is an example setup with a management node at ip 10.4.6.13 and data nodes
at 10.4.6.11 and 10.4.6.12.  This shows the basic flow of a cluster backup.

::

  $ cat > /etc/holland/backupsets/mysql-cluster.conf <<EOF
  [holland:backup]
  plugin = mysql-cluster
  backups-to-keep = 1
  auto-purge-failures = yes
  purge-policy = after-backup
  
  [mysql-cluster]
  connect-string = 10.4.6.13
  default-ssh-user = root
  default-ssh-keyfile = /etc/holland/holland.pkey
  
  [compression]
  method = gzip
  level = 6
  EOF

  $ holland backup mysql-cluster
  Holland 1.0.6 started with pid 11807
  --- Starting backup run ---
  Acquired lock /etc/holland/backupsets/mysql-cluster.conf : '/etc/holland/backupsets/mysql-cluster.conf'
  Creating backup path /var/spool/holland/mysql-cluster/20110316_223610
  Estimated Backup Size: 0.00B
  Starting backup[mysql-cluster/20110316_223610] via plugin mysql-cluster
   + ndb_mgm -c 10.4.6.13 -e "START BACKUP WAIT COMPLETED"
   > Connected to Management Server at: 10.4.6.13:1186
   > Waiting for completed, this may take several minutes
   > Node 3: Backup 142 started from node 1
   > Node 3: Backup 142 started from node 1 completed
   >  StartGCP: 89098 StopGCP: 89101
   >  #Records: 2092802 #LogRecords: 0
   >  Data: 33502780 bytes Log: 0 bytes
   + ndb_config --connect-string=10.4.6.13 --type=ndbd --query=hostname,nodegroup,nodeid,backupdatadir --fields=: --rows=\n
   > 10.4.6.11:0:2:/var/lib/mysql backups
   > 10.4.6.12:0:3:/var/lib/mysql-cluster
   + ssh -o BatchMode=yes -i /etc/holland/holland.pkey root@10.4.6.12 "ls -lah /var/lib/mysql-cluster/BACKUP/BACKUP-142"
   > total 17M
   > drwxr-x---  2 root root 4.0K Mar 16 22:36 .
   > drwxr-x--- 67 root root 4.0K Mar 16 22:36 ..
   > -rw-rw-rw-  1 root root  16M Mar 16 22:36 BACKUP-142-0.3.Data
   > -rw-rw-rw-  1 root root 9.3K Mar 16 22:36 BACKUP-142.3.ctl
   > -rw-rw-rw-  1 root root   52 Mar 16 22:36 BACKUP-142.3.log
   + rsync -avz -e "ssh -o BatchMode=yes -i /etc/holland/holland.pkey" root@10.4.6.12:/var/lib/mysql-cluster/BACKUP/BACKUP-142 /var/spool/holland/mysql-cluster/20110316_223610
   > receiving file list ... done
   > BACKUP-142/
   > BACKUP-142/BACKUP-142-0.3.Data
   > BACKUP-142/BACKUP-142.3.ctl
   > BACKUP-142/BACKUP-142.3.log
   > 
   > sent 92 bytes  received 1861628 bytes  1241146.67 bytes/sec
   > total size is 16751276  speedup is 9.00
  Archived node 10.4.6.12 with backup id 142
   + ssh -o BatchMode=yes -i /etc/holland/holland.pkey root@10.4.6.11 "ls -lah \"/var/lib/mysql backups/BACKUP/BACKUP-142\""
   > total 17M
   > drwxr-x---  2 root root 4.0K Mar 16 22:36 .
   > drwxr-x--- 62 root root 4.0K Mar 16 22:36 ..
   > -rw-r--r--  1 root root  16M Mar 16 22:36 BACKUP-142-0.2.Data
   > -rw-r--r--  1 root root 9.3K Mar 16 22:36 BACKUP-142.2.ctl
   > -rw-r--r--  1 root root   52 Mar 16 22:36 BACKUP-142.2.log
   + rsync -avz -e "ssh -o BatchMode=yes -i /etc/holland/holland.pkey" "root@10.4.6.11:\"/var/lib/mysql backups/BACKUP/BACKUP-142\"" /var/spool/holland/mysql-cluster/20110316_223610
   > receiving file list ... done
   > BACKUP-142/BACKUP-142-0.2.Data
   > BACKUP-142/BACKUP-142.2.ctl
   > BACKUP-142/BACKUP-142.2.log
   > 
   > sent 86 bytes  received 1861875 bytes  1241307.33 bytes/sec
   > total size is 16771024  speedup is 9.01
  Archived node 10.4.6.11 with backup id 142
   + ndb_config --connect-string=10.4.6.13 --type=ndbd --query=hostname,backupdatadir --fields=: --rows=\n
   > 10.4.6.11:/var/lib/mysql backups
   > 10.4.6.12:/var/lib/mysql-cluster
   + ssh -o BatchMode=yes -i /etc/holland/holland.pkey root@10.4.6.12 "rm -fr /var/lib/mysql-cluster/BACKUP/BACKUP-142"
   + ssh -o BatchMode=yes -i /etc/holland/holland.pkey root@10.4.6.11 "rm -fr \"/var/lib/mysql backups/BACKUP/BACKUP-142\""
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.3.Data
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.3.Data:      88.8% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.3.Data.gz
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.ctl
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.ctl:         76.0% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.ctl.gz
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.2.Data
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.2.Data:      88.8% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142-0.2.Data.gz
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.log
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.log:         23.1% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.log.gz
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.log
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.log:         23.1% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.2.log.gz
   + gzip -v -6 /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.ctl
   ! /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.ctl:         76.0% -- replaced with /var/spool/holland/mysql-cluster/20110316_223610/BACKUP-142/BACKUP-142.3.ctl.gz
  Final on-disk backup size 3.59MB
  Backup completed in 8.30 seconds
  Purged mysql-cluster/20110316_222007
  1 backups purged
  Released lock /etc/holland/backupsets/mysql-cluster.conf
  --- Ending backup run ---
  
Reporting Bugs
==============

Report bugs against Delphini to the Holland projects at `launchpad
<http://launchpad.net/holland-backup>_`.

Getting the Code
================

If you want to look at the code for Delphini you can checkout or fork the code
at `GitHub <http://github.com/abg/holland-delphini>`_

