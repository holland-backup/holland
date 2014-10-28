import os, sys
from subprocess import Popen, PIPE
import time
import errno
import fcntl
import logging
from holland.core.command import Command, option, run
from holland.core.backup import BackupRunner, BackupError
from holland.core.exceptions import BackupError
from holland.core.config import hollandcfg, ConfigError
from holland.core.spool import spool
from holland.core.util.fmt import format_interval, format_bytes
from holland.core.util.path import disk_free, disk_capacity, getmount
from holland.core.util.lock import Lock, LockError
from holland.core.util.pycompat import Template

LOG = logging.getLogger(__name__)

class Backup(Command):
    """${cmd_usage}

    Backup the specified backupsets or all
    active backupsets specified in holland.conf

    ${cmd_option_list}

    """

    name = 'backup'

    aliases = [
        'bk'
    ]

    options = [
        option('--abort-immediately', action='store_true',
                help="Abort on the first backupset that fails."),
        option('--dry-run', '-n', action='store_true',
                help="Print backup commands without executing them."),
        option('--no-lock', '-f', action='store_true', default=False,
                help="Run even if another copy of Holland is running.")
    ]

    description = 'Run backups for active backupsets'

    def run(self, cmd, opts, *backupsets):
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]

        if not backupsets:
            LOG.info("Nothing to backup")
            return 1

        runner = BackupRunner(spool)

        # dry-run implies no-lock
        if opts.dry_run:
            opts.no_lock = True

        # don't purge if doing a dry-run, or when simultaneous backups may be running
        if not opts.no_lock:
            purge_mgr = PurgeManager()

            runner.register_cb('before-backup', purge_mgr)
            runner.register_cb('after-backup', purge_mgr)
            runner.register_cb('failed-backup', purge_backup)

        runner.register_cb('after-backup', report_low_space)

        runner.register_cb('before-backup', call_hooks)
        runner.register_cb('after-backup', call_hooks)
        runner.register_cb('failed-backup', call_hooks)

        error = 1
        LOG.info("--- Starting %s run ---", opts.dry_run and 'dry' or 'backup')
        for name in backupsets:
            try:
                config = hollandcfg.backupset(name)
                # ensure we have at least an empty holland:backup section
                config.setdefault('holland:backup', {})
            except (SyntaxError, IOError), exc:
                LOG.error("Could not load backupset '%s': %s", name, exc)
                break

            if not opts.no_lock:
                lock = Lock(config.filename)
                try:
                    lock.acquire()
                    LOG.debug("Set advisory lock on %s", lock.path)
                except LockError:
                    LOG.debug("Unable to acquire advisory lock on %s",
                              lock.path)
                    LOG.error("Another holland backup process is already "
                              "running backupset '%s'. Aborting.", name)
                    break

            try:
                try:
                    runner.backup(name, config, opts.dry_run)
                except BackupError, exc:
                    LOG.error("Backup failed: %s", exc.args[0])
                    break
                except ConfigError, exc:
                    break
            finally:
                if not opts.no_lock:
                    if lock.is_locked():
                        lock.release()
                    LOG.info("Released lock %s", lock.path)
        else:
            error = 0
        LOG.info("--- Ending %s run ---", opts.dry_run and 'dry' or 'backup')
        return error

def purge_backup(event, entry):
    if entry.config['holland:backup']['auto-purge-failures']:
        entry.purge()
        LOG.info("Purged failed backup: %s", entry.name)
    else:
        LOG.info("auto-purge-failures not enabled. Failed backup not purged.")

def call_hooks(event, entry):
    hook = event + "-command"

    if entry.config['holland:backup'][hook] is not None:
        cmd = entry.config['holland:backup'][hook]
        try:
            cmd = Template(cmd).safe_substitute(
                        hook=hook,
                        backupset=entry.backupset,
                        backupdir=entry.path
            )
            LOG.info(" [%s]> %s", hook, cmd)
            process = Popen(cmd,
                            shell=True,
                            stdin=open("/dev/null", "r"),
                            stdout=PIPE,
                            stderr=PIPE,
                            close_fds=True)
            output, errors = process.communicate()
        except OSError, exc:
            raise BackupError("%s", exc)

        for line in errors.splitlines():
            LOG.error(" ! %s", line)
        for line in output.splitlines():
            LOG.info(" + %s", line)
        if process.returncode != 0:
            raise BackupError("%s command failed" % hook)
    return 0

class PurgeManager(object):
    def __call__(self, event, entry):
        purge_policy = entry.config['holland:backup']['purge-policy']

        if event == 'before-backup' and purge_policy != 'before-backup':
            return
        if event == 'after-backup' and purge_policy != 'after-backup':
            return

        backupset = spool.find_backupset(entry.backupset)
        if not backupset:
            LOG.info("Nothing to purge")
            return

        retention_count = entry.config['holland:backup']['backups-to-keep']
        retention_count = int(retention_count)
        if event == 'after-backup' and retention_count == 0:
            # Always maintain latest backup
            LOG.warning("!! backups-to-keep set to 0, but "
                        "purge-policy = after-backup. This would immediately "
                        "purge all backups which is probably not intended. "
                        "Setting backups-to-keep to 1")
            retention_count = 1
        if event == 'before-backup':
            retention_count += 1
        self.purge_backupset(backupset, retention_count)
        backupset.update_symlinks()

    def purge_backupset(self, backupset, retention_count):
        purge_count = 0
        for backup in backupset.purge(retention_count):
            purge_count += 1
            LOG.info("Purged %s", backup.name)

        if purge_count == 0:
            LOG.info("No backups purged")
        else:
            LOG.info("%d backups purged", purge_count)

def report_low_space(event, entry):
    total_space = disk_capacity(entry.path)
    free_space = disk_free(entry.path)
    if free_space < 0.10*total_space:
        LOG.warning("Extremely low free space on %s's filesystem (%s).",
                    entry.path,
                    getmount(entry.path))
        LOG.warning("%s of %s [%.2f%%] remaining",
                    format_bytes(free_space),
                    format_bytes(total_space),
                    (float(free_space) / total_space)*100)
