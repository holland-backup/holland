import urllib
import logging

from pymongo import MongoClient


LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[mongodump]
host = string(default=None)
username = string(default=None)
password = string(default=None)
authenticationDatabase = string(default=None)
""".splitlines()

class MongoDump(object):
    "MongoDB backup plugin for holland"

    def __init__(self, name, config, target_directory, dry_run=False):
        """Createa new MongoDump instance

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
        ret = 0

        uri = "mongodb://"
        username = self.config["mongodump"].get("username")
        if username:
            uri += urllib.quote_plus(username)
            password = self.config["mongodump"].get("password")
            if password:
                uri += urllib.quote_plus(password)
            uri += '@'
        uri += self.config["mongodump"].get("host")
        client = MongoClient(uri)
        dbs = client.database_names()
        for db in dbs:
            c = client[db]
            tup = c.command("dbstats")
            ret += tup["storageSize"]
        return ret

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
        return "MongoDB using mongodump plugin"
