.. _command-line-reference:

Holland Command-Line Reference
======================================
Here are the commands available from the 'holland' command-line tool:

help (h)
--------
**Usage**: ``holland help <command>``

Provides basic information about the provided command. If no command is
provided, it displays global help instead.

backup (bk)
-----------
**Usage:** ``holland backup [backup-set1, backup-set2, ..., backup-setN]``

Runs the backup operation. If no backup-sets are specified, 
all active backup-sets (those defined in the 'backupsets' variable in
holland.conf) are backed up.

One or more backup-sets can be specified directly, in which case only those
backup-sets are backed up.

Additional Command Line Arguments:

``--dry-run`` (``-n``): Can be used here to simulate, but not actually 
run, a backup. This should be used when troubleshooting a particular error 
before trying to run a real backup.

``--no-lock`` (``-f``): Normally, only one instance of Holland can run at any 
given time using lock-files. Using this flag causes the lock-files to be 
ignored. This has some very clear use-cases but otherwise be mindful of using 
this setting as it can cause backups to fail in some cases.

``--abort-immediately``: abort on the first backup-set that fails (assuming
multiple backupsets were specified)

**Examples**:

``# holland bk --dry-run weekly``: Attempts a dry-run of the weekly
backup-set.

``# holland bk --no-lock --abort-immediately``: Attempts a backup of all
the default backup-sets ignoring locks and aborting immediately if one of the
backup-sets fails.

list-backups (lb)
-----------------
**Usage:** ``holland list-backups``

Provides extended information about available backups.

list-plugins (lp)
-----------------
**Usage**: ``holland list-plugins``

Lists all the available (installed) plugins available to Holland.

mk-config (mc)
--------------
**Usage:** ``holland mk-config <provider>``

Generates a template backup-set for a particular provider (such as mysqldump).
By default, the output is sent to standard out but can be copied to a file, 
either by using the ``--file``, ``--edit``, or ``-name`` options (see
below).

Additional Command Line Arguments:

``--edit``: Load the file into the system text-editor for further 
modifications.

``--file=FILE`` (``-f``): Write the output directly to provided file.

``--name=NAME``: Creates a backup-set usable in Holland, which basically
means that a file is created of the provided name under the backup-set
directory.

``--provider``: Indicates that the default provider configuration should
be outputted instead. This is really only used when creating a provider
config specifically - it should not be used for backup-sets.

**Examples**:

``# holland mk-config mysql-lvm > mysql-lvm.conf``: Output the default
configuration for MySQL-LVM backups and write the contents out to
mysql-lvm.conf in the current working directory.

``# holland mc mysqldump --name=Bob --edit``: Create a backup-set using
the mysqldump provider named Bob and allow interactive editing of the 
backup-set before saving the file.

purge (pg)
----------
**Usage:** ``holland purge <backup-set>/<backup-id>``

Purges old backups by specifying the backup-set name and set-id. 

For example:
``# holland purge mybackups/20090502_155438``: Purge one of the backups
taken on May 2nd, 2009 from the mybackups backup-set.
