.. _config-xtrabackup:

Xtrabackup Provider Configuration [xtrabackup]
==============================================

**global-defaults** = <path> (default: /etc/my.cnf)

    The MySQL configuration file for xtrabackup to parse.  This is !include'd
    into the my.cnf the xtrabackup plugin generates

**innobackupex** = <name> (default: innobackupex-1.5.1)

    The path to the innobackupex script to run. If this is a relative path
    this will be found in holland's environment PATH as configured in
    /etc/holland/holland.conf.
    
    
**ibbackup** = <name>    
    
    The path to the ibbackup command to use.  By default, no --ibbackup option
    is pass to the innobackupex script.  Usually innobackupex will detect this
    by itself and this should not need to be set.

**stream** = tar|xbstream|yes|no (default: tar)

    Whether to generate a streaming backup. 

.. versionchanged:: 1.0.8
   'tar' and 'xbstream' are now valid options.  The old stream = yes is
   now equivalent to stream = tar and stream = no disables streaming
   entirely and will result in a normal directory copy with xtrabackup
       

**apply-logs** = yes | no (default: yes)

    Whether to run ``innobackupex --apply-logs`` at the end of the backup. This
    is only supported when performing a non-streaming, non-compressed backup.
    In this case, even if apply-logs = yes (the default), the prepare stage
    will be skipped.  Even with an uncompressed, non-streaming backup you may
    want to disable apply-logs if you wish to use incremental backups.

    .. versionadded:: 1.0.8

**slave-info** = yes | no (default: yes)
    
    Whether to enable the --slave-info innobackupex option

**safe-slave-backup** = yes | no (default: yes)
    
    Whether to enable the --safe-slave-backup innobackupex option.

**no-lock** = yes | no (default: no)

    Whether to enable the --no-lock innobackupex option

**tmpdir** = <path> (default: ``${backup_directory}``)

    The path for the innobackupex --tmpdir option. By default this will use the
    current holland backup directory to workaround the following bug:
    https://bugs.launchpad.net/percona-xtrabackup/+bug/1007446

    .. versionadded:: 1.0.8

**additional-options** = <option>[, <option>...]

    A list of additional options to pass to innobackupex.  This is a comma
    separated list of options.

**pre-command** = <command-string>

    A command to run prior to running this xtrabackup run.  This can be used,
    for instance, to generate a mysqldump schema dump prior to running
    xtrabackup.  instances of ${backup_directory} will be replaced with the
    current holland backup directory where the xtrabackup data will be stored.


[compression]
-------------
.. toctree::
    :maxdepth: 1

    compression

[mysql:client]
--------------
.. toctree::
    :maxdepth: 1

    mysqlconfig
