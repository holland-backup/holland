from collections import namedtuple
from datetime import timedelta, datetime

from holland.core.spool import spool
from holland.core.config import hollandcfg

from holland.core.command import Command, option


class Nagios(Command):
    """${cmd_usage}

    ${cmd_option_list}

    Check backup retention
    """
    name = 'nagios'
    aliases = []
    description = 'Check backup retention'
    options = [
            option('-r', '--retention', type="int", default=2,
                help="Number of days expected in backup"),
            option('-m', '--minimum-age', type="int", default=1,
                help="At least one backup must be newer that this in days"),
            option('-c', '--copies', type="int",
                help="Minimum number of copies in retention." \
                        "Default 'backups-to-keep'"),
    ]

    def run(self, cmd, opts, *backupsets):
        # check parameters
        if opts.retention < 0:
            print "HOLLAND ERROR retention must be greater or equal 0"
            return 2
        if opts.minimum_age < 0 or opts.minimum_age > opts.retention:
            print "HOLLAND ERROR minimum age must be positive and lower than retention"
            return 2

        
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]
        if not backupsets:
            print "HOLLAND WARNING - No backupsets"
            return 1

        Retention = namedtuple("Retention",
                ["backupset", "result", "message"])
        info = set()
        for name in backupsets:
            try:
                config = hollandcfg.backupset(name)
            except (Exception), ex:
                info.add(Retention(name, False, str(ex)))
                continue
            # ensure we have at least an empty holland:backup section
            config.setdefault('holland:backup', {})

            backups = list(spool.list_backups(name))

            newer = datetime.fromtimestamp(float(0))
            older = datetime.now()
            for backup in backups:
                backup.load_config()
                str_d = backup.config['holland:backup']['stop-time']
                d = datetime.fromtimestamp(float(str_d))
                if d > newer:
                    newer = d
                if d < older:
                    older = d

            copies = int(opts.copies) if opts.copies \
                    else int(config['holland:backup']['backups-to-keep'])

            message = "{} of {}".format(len(backups), copies)
            status = len(backups) >= copies

            retention = datetime.now() - timedelta(days=opts.retention)
            minimum_age = datetime.now() - timedelta(days=opts.minimum_age)
            if older > retention:
                message += '; backup out of retention: ' \
                        'expected older than {}, got {}'.format(
                        retention, older)
                status = False
            if newer < minimum_age:
                message += '; backup out of retention: ' \
                        'expect earlier than {}, got {}'.format(
                        minimum_age, newer)
                status = False

            info.add(Retention(name, status, message))

        errors = [x for x in info if not x.result]

        if errors:
            print "HOLLAND ERROR - Out of retention: {}".format(
                    [(x.backupset, x.message) for x in errors])
            return 2
        else:
            print "HOLLAND OK - All backups in retention"

        return 0
