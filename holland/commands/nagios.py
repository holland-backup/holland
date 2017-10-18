from collections import namedtuple

from holland.core.spool import spool
from holland.core.config import hollandcfg

from holland.core.command import Command

class Nagios(Command):
    """${cmd_usage}                                 

    ${cmd_option_list}                              

    Check backup retention                          
    """                                             
    name = 'nagios'                                 
    aliases = []                                    
    description = 'Check backup retention'          

    def run(self, cmd, opts):                       
        backupsets = hollandcfg.lookup('holland.backupsets')
        # strip empty items from backupsets list
        backupsets = [name for name in backupsets if name]
        if not backupsets:
            print "HOLLAND WARNING - No backupsets"
            return 0

        Retention = namedtuple("Retention", ["backupset", "result", "message"])
        info = set()
        for name in backupsets:
            try:
                config = hollandcfg.backupset(name)
            except (Exception), ex:
                info.add(Retention(name, False, str(ex)))
                continue
            # ensure we have at least an empty holland:backup section
            config.setdefault('holland:backup', {})

            backups = len(list(spool.list_backups(name)))
            retention = int(config['holland:backup']['backups-to-keep'])
            message = "{} of {}".format(backups, retention)
            info.add(Retention(name, backups >= retention, message))

        errors = [x for x in info if not x.result]

        if errors:
            print "HOLLAND ERROR - Out of retention: {}".format(
                    [(x.backupset, x.message) for x in errors])
        else:
            print "HOLLAND OK - All backups in retention"

        return 0
