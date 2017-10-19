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
            option('-t', '--threshold', type="int", default=2,
                help="If all backups in a backupset are older than this " +
                "number in days consider out of retention")
    ]

    def run(self, cmd, opts, *backupsets):
        if not backupsets:
            backupsets = hollandcfg.lookup('holland.backupsets')

        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]
        if not backupsets:
            print "HOLLAND WARNING - No backupsets"
            return 0

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

            most_recent = datetime.fromtimestamp(float(0))
            for backup in backups:
                backup.load_config()
                str_d = backup.config['holland:backup']['stop-time']
                d = datetime.fromtimestamp(float(str_d))
                if d > most_recent:
                    most_recent = d

            n_retention = int(config['holland:backup']['backups-to-keep'])
            message = "{} of {}".format(len(backups), n_retention)
            status = len(backups) >= n_retention

            threshold = datetime.now() - timedelta(days=opts.threshold)
            if most_recent < threshold:
                message += '; backups too old: expected {} got {}'.format(
                        threshold, most_recent)
                status = False
            info.add(Retention(name, status, message))

        errors = [x for x in info if not x.result]

        if errors:
            print "HOLLAND ERROR - Out of retention: {}".format(
                    [(x.backupset, x.message) for x in errors])
        else:
            print "HOLLAND OK - All backups in retention"

        return 0
