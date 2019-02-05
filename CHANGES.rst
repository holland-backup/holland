=======
CHANGES
=======

LP# refers to holland launchpad bugs here: 
http://bugs.launchpad.net/holland-backup

GH# referes to the deprecated github bug tracker here:
https://github.com/holland-backup/holland/issues

1.1.12 - Feb 1, 2019
---------------------

holland
+++++++

- Start on new release

1.1.11 - Jan 23, 2019
---------------------

holland
+++++++

- Fixes #260
- Rework and lint holland_commvault
- holland_commvault now required pid module
- Remove warning message and logging error when dumps contain an invalid view

1.1.10 - Dec 10, 2018
---------------------

holland
+++++++

- Rework mysqldump dry-run function

1.1.9 - Dec 12, 2018
---------------------

holland
+++++++

- Remove mock bundled library from holland.backup.mysqldump
- General code improvements
- Allow users to define the mysql log in holland.backup.mysql_lvm

1.1.8 - Oct, 2018
---------------------

holland
+++++++

- Bug fix release


1.1.1 - Aug 6, 2018
---------------------

holland
+++++++

- Remove unused files and modules
- Move from optparse to argparse
- Remove help command as this functionality is built into argparse
- Update code base to pass pylint checks
- Add historic-size option under 'holland:backup' in backupset, this will use the last
  backups size to estimate the next backup size. Holland will default to the current estimate
  method if it can't determine what the last values were, or if the database size has changed
  drastically


1.1.0 - May 8, 2018
---------------------

holland
+++++++

holland
+++++++

- Update Holland to work on Python 3. It's now using compatibility library to support Python version > 2.6
- Update packaged version of ConfigObj to 5.0.6 
- holland now has a few external dependencies: 
  * future 
  * six 
- Implemented fix for broken stop-slave function on MySQL 5.7+ (Fixes GH#185 jacripe)
- Remove holland.backup.maatkit and holland.backup.mysqlhotcopy from active backup list
- Add 'format' option to 'logging' in /etc/holland/holland.conf (GH#99).
  This uses the current log formatter if 'format' not defined.

holland-mysqldump
+++++++++++++++++

- Add dir archive-method (GH Pull #184 chder)
- bin-log-position will now record the masters position even if stop-slave isn't enabled
- Update stop/start slave fuctions

holland-xtrabackup
+++++++++++++++++

- Print out xtrabackup version number

holland-mariabackup
+++++++++++++++++

- Add plugin to allow use of mariabackup binary

holland-mongodb
+++++++++++++++++

- Add plugin to allow holland to backup mongodb

1.0.14 - Nov 17, 2016
---------------------

holland
+++++++

- A fix for launchpad bug #1220841 caused plugins that used
  "SHOW SLAVE STATUS" via the holland mysql lib to fail with
  an "unknown encoding: binary" error.  The changes for 
  LP #1220841 have been reverted.

holland-mysqldump
+++++++++++++++++

- A bug was introduced in 1.0.12 which caused mysqldump's lock-method
  "auto-detect" option to always use lock-tables under MySQL 5.0
  environments. (Fixes GH#148)


1.0.12 - Feb 8, 2016
--------------------

holland
+++++++
- The "holland" command no longer attempts to suppress log output when output
  is not to a terminal. Previously this was done when either the --quiet
  options was used or if holland detected it was not writing to a console.
  Now the "holland --quiet" option must be used to suppress output or output
  can be redirected via standard shell stdio facilities.
  (Fixes GH#98)
- Hooks are no longer run during a dry-run (Fixes GH#121; Thanks Mike Griffin!)
- Holland now supports gpg as a compression option for all backup
  plugins (Thanks to Ryan Cleere for the contribution and Tim Soderstrom
  for documenting the improvement) GH#95
- Added contrib/holland-commvault; See contrib/holland-commvault/README
  for a description of this module.

holland-mysqldump
+++++++++++++++++
- Various MySQL metadata queries used by the mysqldump plugin
  were not compatible with MySQL-python 1.2.5 due to the
  way parameters were passed. (Fixes GH#106).
- exclude-invalid-views will now handle invalid views using
  an illegal mix of collation (Fixes LP#1207852).
- exclude-invalid-views handles unexpected mysql errors more
  gracefully now. (Fixes LP#1207852)
- lock-method = auto-detect now considers memory, myisam_mrg
  and federated engines as transactional when determining
  whether to use mysqldump --single-transaction  (LP #1081261)
- mysqldump failed to detect invalid views under mysql 5.0
  (LP #1262352)
- invalid strings in show slave status are now handled more
  gracefully (LP #1220841)
- Estimating the size of a backup would fail under MariaDB 10.1
  due to the numeric value being returned as a Decimal rather
  than an int object, primarily causing later formatting of
  the estimated values to fail due to mixing decimal and
  integer arithemetic.  holland now ensures these values
  are integers.  (GH#125)

holland-pgdump
++++++++++++++
- missing pg_dump/pg_dumpall commands are now handled more gracefully
  (LP #1206202)
- The connection used for discovering databases to backup is now
  closed before pg_dump commands are run (LP #1236618)
- special characters in the provided password are escaped when
  generating PGPASSFILE. (GH#116)

holland-xtrabackup
++++++++++++++++++
- holland-xtrabackup now uses innobackupex as innobackupex binary
  as innobackupex-1.5.1 has been deprecated upstream for several
  releases
- holland-xtrabackup previously failed to compress xbstream
  archives regardless of the [compression] configuration for
  the backupset.  (LP#1246562)

1.0.10 - Jul 29, 2013
---------------------

holland
+++++++
- Added purge-on-demand option to [holland:backup]
  If set, this option will cause holland backup to attempt to purge old backups
  to allow a new backup to start rather than failing when it appears that
  there is insufficient space to run a new backup.
  If the space consumed by all purgable backups is less than the estimated
  space for a new backup, no backups are purged.

holland-common
++++++++++++++
- FLUSH TABLES is now run as FLUSH /\*!40101 LOCAL \*/ TABLES to avoid
  replicating this statement.  This affects any plugins that issue flush
  tables via the holland-common mysql client API

- [compression] config sections now support an additional parameter
  "options".  This extends the commandline for the underlying compression
  command.  This was added to allow specifying command specific options
  such as gzip --rsyncable or pigz -p N.
  

holland-mysqldump
+++++++++++++++++
- dump-events now defaults to on - automatically disabled for MySQL < 5.1
- dump-routines now defaults to on - automatically disabled for MySQL < 5.0
- when no databases are found during schema discovery, mysqldump now fails
  with a backup error.  This can occur if the configured backup user does
  not have sufficient access to any database.

1.0.8 - Mar 7, 2013
-------------------

holland
+++++++
- Fixed bug in purge-policy=before-backup that would fail to retain the
  in-progress backup and ultimately cause the backup run to fail.
- Added before/after/failed backup command options to [holland:backup] for 
  each backupset. Contributed by osheroff
- Fixed a bug in holland.conf [logging] handling where the log-level would be
  ignored in favor of the default value for holland --log-level.
- holland mk-config now adds a default estimated-size-factor to the 
  [holland:backup] section.
- holland purge now correctly updates symlinks when run manually

holland-common
++++++++++++++

- pbzip2 is now a supported compression option.  This is valid for any holland
  plugins that use the internal holland compression command api.
  Contributed by justino

holland-mysqldump
+++++++++++++++++
- Fix bug with holland backup --dry-run and mysqldump plugin's stop-slave=yes
  option.  The slave would be incorrectly stopped in dry-run mode, but never
  restarted.
- Fixed a bug with estimate-method=const where lock-method=auto-detect would
  not properly detect when to set single-transaction because table engine
  information was not read.
- Plugin estimate method now ignores MRG_MyISAM and Federated tables when
  estimating the total backup space in order to avoid counting tables twice.
- Fixed a bug in my.cnf parsing code that did not treat my.cnf sections case
  insenstiviely.  This differed from the mysqldump behavior

holland-mysqllvm
++++++++++++++++
- Fixed a bug in the relpath implementation where paths relative to / were not
  properly calculated.  This was a bug in os.path.relpath in python <= 2.6:
  http://bugs.python.org/issue5117.  Backported the fix from python 2.7
- Fix a bug in tar archiver that was not closing the output stream at the end
  of a backup.
- Added pre- and post-args to [tar] config to allow customizing options to GNU
  tar used for archiving mysql-lvm backups.
- LVM plugins now detect when they cannot correctly backup innodb data.
  mysql-lvm will abort by default if any innodb data files reside outside the
  datadir. mysqldump-lvm will rewrite innodb-data-file-path,
  innodb-data-home-dir and innodb-log-group-home-dir in order to startup the
  bootstrap mysqld process correctly.
- added force-innodb-backup option to force a mysql-lvm backup even if it
  appears unsafe to do so.  InnoDB datafiles outside of the datadir are not
  backed up by default unless tar's pre- and/or post-args are set correctly.
- added force-backup-to-snapshot-origin option to disable sanity check when
  holland's backup-directory is set to store backups on the same volume we are
  currently snapshotting.

holland-xtrabackup
++++++++++++++++++
- The xtrabackup plugin now fails more cleanly when the innbackupex command
  could not be found
- The xtrabackup plugin now handles failures in closing the output stream more
  gracefully.
- Updated xtrabackup plugin to support xtrabackup 2.0
- Added stream=xbstream support
- Added support for streaming=no to perform a simply directory copy backup
- Added tmpdir option - previously tmpdir was taken from the my.cnf
  defaults-file
- Added an additional-options = option, option, option for specifying
  arbitrary options to innobackupex
- Added ibbackup=path option
- Added pre-command=command option
- Added safe-slave-backup=boolean option
- Added apply-logs=boolean option


1.0.6 - Jan 12, 2011 
--------------------

holland
+++++++
- holland backup better differentiates between a dry-run and normal backup
  in logging output
- holland mk-config now produces cleaner output and includes a --minimal
  option to strip comments from the backupset output.
- holland now more elegantly handles running the same backupset more than
  once per second.  Previously this could result in a stack trace as the
  backupset directory already exists.
- holland now maintains newest and oldest symlinks in each backupset
  directory pointing to the newest and oldest backup.
  (Contribution from Micah Yoder)
- holland.conf now accepts a tmpdir option for environments where
  manipulating TEMPDIR environment variable is not convenient
- holland backup --help is now consistent with holland help backup
  (Fixes LP#677716)
- holland now warns about unknown options in config files
- The example plugin has been deprecated in favor of the holland-random
  plugin, which provides a more useful starting example
- previously when logging failed (disk space, permissions, etc.) a stack
  trace would be printed on stderr.  As of 1.0.6 this is only done in when
  the logging level is set to 'debug'
- holland backup --dry-run previously failed for mysqldump backups when 
  per-table exclusions were specified. (Fixes GH#60)
- config files are now read as utf8 (Fixes GH#57)


holland-mysqldump
+++++++++++++++++
- holland-mysqldump now only stops the SQL_THREAD when stop-slave is 
  requested
- error messages from MySQLdb are now decoded from utf8 as necessary
- holland-mysqldump now defaults max-allowed-packet to 128M
- holland-mysqldump now excludes performance_schema by default
- holland-mysqldump now more reliably parses my.cnf files specified via
  defaults-extra-files


holland-mysqllvm
++++++++++++++++
- when a volume group has zero free extents, an unhandled exception would be
  thrown due to a bug in formatting the error message (Fixed LP#699795)
- holland-mysqllvm had a bug in the example config file that would always
  maintain two backups
- holland-mysqllvm now catches SIGHUP/SIGTERM more consistently
- holland-mysqllvm logs error output from various commands more consistently
- holland-mysqllvm will not create snapshot-mountpoint if it does
  not exist (Fixes LP#671965)
- holland-mysqllvm previously failed to automatically mount xfs snapshots
  with nouuid.  This is now automatically detected (Fixes GH#61)
- additional tests for ext3 and xfs filesystems were added to holland.lib.lvm


holland-xtrabackup
++++++++++++++++++
- holland-xtrabackup now logs stderr output on a backup failure. Previously
  this was only logged to xtrabackup.log in the backup directory.
  (Fixes LP#671971)
- holland-xtrabackup should now be built by default in contrib/holland.spec


holland-sqlite
++++++++++++++
- add missing inline compression option.


holland-pgdump
++++++++++++++
- Added holland-pgdump plugin (Contribution from Micah Yoder)


