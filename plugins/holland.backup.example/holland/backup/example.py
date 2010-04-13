import logging

LOGGER = logging.getLogger(__name__)
class Example(object):
    def __init__(self, name, config, target_directory, dry_run=False):
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        LOGGER.info("initializing")
        if dry_run:
            LOGGER.info("dry-run mode")

    def estimate_backup_size(self):
        return 0

    def backup(self):
        """
        Do what is necessary to perform and validate a successful backup.
        """
        LOGGER.info("this plugin does nothing")

    def cleanup(self):
        """
        Cleanup from backup stage
        """
        LOGGER.info("nothing to cleanup")

def provider(*args, **kwargs):
    return Example(*args, **kwargs)
