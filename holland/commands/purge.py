import os
import sys
import logging
import readline
from holland.core.command import Command, option
from holland.core.config import hollandcfg
from holland.core.spool import spool

LOGGER = logging.getLogger(__name__)

class Purge(Command):
    """${cmd_usage}

    Purge the requested job runs 

    ${cmd_option_list}
        
    """

    name = 'purge'

    aliases = [
        'pg'
    ]

    options = [
        option('--dry-run', '-n', action='store_true',
                help="Print what would be purged without actually purging"),
        option('--full', action='store_true',
                help="Purge every backup for the specified job run(s)"),
        option('--force', action='store_true',
               help="Do not prompt for confirmation")
    ]

    description = 'Purge the requested job runs'
    
    def _purge_all(self, opts):
        for backupset in spool:
            backup_list= backupset.list_backups()
            for backup in backup_list:
                # check if the run completed
                # holland:backup.stop > 0?
                # otherwise, partial - purge
                if not os.path.exists(backup.config.filename):
                    print >>sys.stderr, "Purging broken backup %s" % \
                                         backup.name
                    backup.purge()
                else:
                    print >>sys.stderr, "Skipping backup %s" % backup.name

    # if job_run is given we purge everything but the latest backup
    # for that job
    # if not defined, we run through all jobs and purge everything
    # but the latest backup on each
    # Maybe have an option '--full' that purges *everything*
    def run(self, cmd, opts, *backups):
        if not backups:
            self._purge_all(opts)
        else:
            bks = []
            for backup in backups:
                bk = spool.find_backup(backup)
                if bk is None:
                    print >>sys.stderr, "Did not find backup called %s" % \
                                         backup
                else:
                    print "Found backup: %s\n" % bk
                    bks.append(bk)
            
            if not bks:
                return 1

            if opts.dry_run:
                for bk in bks:
                    print "[Dry-run] Purging %s [%s]" % (bk, bk.path)
                return 0
            else:
                if not opts.force:
                    print "The following backups will be purged:\n"
                    for bk in bks:
                        print "%s\n" % bk
                    print "This will completely destroy data locally " + \
                          "on this server.\n"
                    confirm = raw_input("Are you sure you want to do " + \
                                        "this? [N/y] ")
                    if confirm.lower() not in ['y', "yes", "ya", "yea",
                                               "hell yea"]:
                        return 1

                    print ""

                for bk in bks:
                    print "Purging %s\n" % bk
                    bk.purge()
