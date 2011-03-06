Holland Backup Hooks
=====================

Hooks are actions to perform as various points during the backup process. There
are currently 4 events that can have hooks run:

  * setup               - before any configuration of a plugin is done
  * pre-backup          - before the backup process is started
  * backup-failure      - after a backup has failed
  * post-backup         - after a backup has completed successfully

Events are configured by providing a list of configuration sections via the
``hooks`` option in the ``[holland:backup]`` section of a backupset config
file.  Each item is the name of a section that will hold the hook's config
options.  

Example
-------

Here is a quick example of a mysqldump backup that runs a pre and post command.

::

  [holland:backup]
  plugin = mysqldump
  hooks = pause-monitoring, resume-monitoring
  ...

  [pause-monitoring]
  plugin = command
  event = before-backup
  cmd = touch /tmp/monitor.stop

  [resume-monitoring]
  plugin = command
  event = after-backup
  cmd = rm -f /tmp/monitor.stop

In this example two hooks are defined ``pause-monitoring`` and
``resume-monitoring``.  These names map to two config sections: 
``[pause-monitoring]`` and ``[resume-monitoring]`` respectively
that define the actual hook configurations.

In both examples the hook plugin being use is the 'command' plugin. This is
a hook plugin included with holland 1.1 that will execute arbitrary shell
commands at the requested backup events.  Here we touch a file that tells
some external monitoring script to stop logging errors - perhaps mysqldump
will lock the database for some time or increase load and we don't care
about alerts while this is running.  Afterwards the ``[resume-monitoring]``
hook will be called once a backup completes and remove the sentinel file.


Config File Syntax
------------------

As shown in the previous example hook plugins are simple config file sections
defined as a list in the ``[holland:backup]`` section.  The hook config
section defines at minimum ``plugin`` noting which hook plugin to use and
some options to customize the behavior of that hook.

So the general format of a backupset with hooks will be:

::

  [holland:backup]
  plugin = <backup-plugin-name>
  hooks = <section>[, <section>...]

  [<name>]
  plugin = <hook-plugin-name>
  <hook-options>

Standard Hooks
--------------

There are a few hooks that are provided by holland.  More can be added by
installing additional hook plugins.  See the developer documentation for
more information on writing hook plugins.

.. describe:: holland.hooks.command

The command hook run an arbitrary shell command at the configured backup
events.  This hook plugin supports the following options:

  events = after-backup | before-backup (default: after-backup)
  cmd    = <command string>
  shell  = <shell interpreter> (default: /bin/sh)
