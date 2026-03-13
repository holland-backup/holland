"""
Example Backup Plugin
"""
import logging

LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[example]
foo_param = boolean(default=no)
""".splitlines()


class ExamplePlugin:
    """An example backup plugin for holland"""

    def __init__(self, name, config, target_directory, dry_run=False):
        """Createa new ExamplePlugin instance

        :param name: unique name of this backup
        :param config: dictionary config for this plugin
        :param target_directory: str path, under which backup data should be
                                 stored
        :param dry_run: boolean flag indicating whether this should be a real
                        backup run or whether this backup should only go
                        through the motions
        """
        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        LOG.info("Validating config")
        self.config.validate_config(CONFIGSPEC)

    def estimate_backup_size(self):
        """Estimate the size (in bytes) of the backup this plugin would
        produce, if run.

        :returns: int. size in bytes
        """
        LOG.info("Example plugin - size of %s", self.name)
        return 0

    def backup(self):
        """
        Do what is necessary to perform and validate a successful backup.
        """
        if self.dry_run:
            LOG.info("[Dry run] Example Plugin - test backup run")
        else:
            LOG.info("Example plugin - real backup run")

    def info(self):
        """Provide extra information about the backup this plugin produced

        :returns: str. A textual string description the backup referenced by
                       `self.config`
        """
        LOG.info("Example plugin - Info for %s", self.name)
        return "Example plugin"
