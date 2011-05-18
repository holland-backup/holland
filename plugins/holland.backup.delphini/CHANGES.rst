1.0.2
=====
- Treat any unavailable node as a failure.  This can happen if we cannot
  ssh/rsync from a server after performing START BACKUP.
- Integration into main holland tree

1.0.1
=====
- log the stop-gcp value from backup output to a replication.info file
  in the backup directory

1.0
===
- initial mysql-cluster plugin implementation
