import os, sys
import time
import errno
import fcntl
import logging
from holland.core.command import Command, option
from holland.core.backup import backup
from holland.core.exceptions import BackupError
from holland.core.config import hollandcfg
from holland.core.spool import spool
from holland.core.util.fmt import format_interval

LOGGER = logging.getLogger(__name__)

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
        option('--no-lock', '-f', action='store_true',
                help="Run even if another copy of Holland is running.")
    ]

    description = 'Run backups for active backupsets'

    def run(self, cmd, opts, *backupsets):
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = filter(lambda x: x, backupsets)

        LOGGER.info("-----> Starting backup run <----")
        if not backupsets:
            LOGGER.info("No backupsets defined.  Please specify in %s or "
                        "specify a name of a backupset in %s",
                        hollandcfg.filename,
                        os.path.join(os.path.dirname(hollandcfg.filename), 'backupsets'))
            return 1

        spool.base_path = hollandcfg.lookup('holland.backup-directory')

        config_file = open(hollandcfg.filename, 'r')
        try:
            fcntl.flock(config_file, fcntl.LOCK_EX|fcntl.LOCK_NB)
            LOGGER.info("Acquired backup lock.")
        except IOError, exc:
            LOGGER.info("Another holland backup appears already be running.")

            if opts.no_lock:
                LOGGER.info("Continuing due to --no-lock")
            else:
                LOGGER.info("Aborting")
                return 1

        error_found = 0
        start_time = time.time()
        try:
            for jobname in backupsets:
                error_found |= run_backup(jobname, opts.dry_run)
                if error_found and opts.abort_immediately:
                    LOGGER.info("Aborting as --abort-immediately is set")
                    break
        finally:
            if not opts.no_lock:
                try:
                    fcntl.flock(config_file, fcntl.LOCK_UN)
                except OSError, exc:
                    LOGGER.debug("Error when releasing backup lock: %s", exc)
                    pass

        if not error_found:
            LOGGER.info("All backupsets run successfully")
        else:
            LOGGER.info("One or more backupsets failed to run successfully")
        LOGGER.info("This backup run of %d backupset%s took %s",
                    len(backupsets), ('','s')[len(backupsets) > 1],
                    format_interval(time.time() - start_time))
        LOGGER.info("-----> Ending backup run <----")
        return error_found


def run_backup(jobname, dry_run=False):
    try:
        backup(jobname, dry_run)
    except KeyboardInterrupt, e:
        LOGGER.info("Interrupt")
    except BackupError, exc:
        LOGGER.error("Backup %r failed: %s", jobname, exc)
    except Exception, exc:
        LOGGER.error("Unexpected exception caught.  This is probably "
                     "a bug.  Please report to the holland "
                     "development team.", exc_info=True)
    else:
        return 0

    return 1
