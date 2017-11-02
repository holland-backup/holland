import logging
import os
import os.path
import subprocess
import urllib

from functools import partial

from pymongo import MongoClient

from holland.core.exceptions import BackupError
from holland.lib.compression import open_stream


LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[mongodump]
host = string(default=None)
username = string(default=None)
password = string(default=None)
authenticationDatabase = string(default=None)

[compression]
method = option('gzip', 'gzip-rsyncable', 'bzip2', 'pbzip2', 'lzop', 'lzma', 'pigz', 'none', default='gzip')
level = integer(min=0, default=1)
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
                uri += ":" + urllib.quote_plus(password)
            uri += '@'
        uri += self.config["mongodump"].get("host")
        client = MongoClient(uri)
        dbs = client.database_names()
        for db in dbs:
            c = client[db]
            tup = c.command("dbstats")
            ret += int(tup["storageSize"])
        # Give an upper estimate to make sure that we have enough disk space
        return ret * 2

    def backup(self):
        """
        Do what is necessary to perform and validate a successful backup.
        """
        command = ["mongodump"]
        username = self.config["mongodump"].get("username")
        if username:
            command += ["-u", username]
            password = self.config["mongodump"].get("password")
            if password:
                # TODO: find a better way to inform the password
                command += ["-p", password]
        command += ["--host", self.config["mongodump"].get("host")]
        command += ["--out", self.target_directory]

        if self.dry_run:
            LOG.info("[Dry run] MongoDump Plugin - test backup run")
            LOG.info("MongoDump command: %s" % subprocess.list2cmdline(command))
        else:
            LOG.info("MongoDump command: %s" % subprocess.list2cmdline(command))
            logfile = open(os.path.join(self.target_directory, "mongodump.log"), "w")
            p = subprocess.Popen(command, stderr=logfile)
            ret = p.wait()
            
            if ret != 0:
                raise BackupError("Mongodump returned %d" % ret)

            zopts = self.config['compression']
            for root, _, files in os.walk(self.target_directory):
                for f in files:
                    path = os.path.join(root, f)
                    ostream = open_stream(path, 'w',
                            method=zopts['method'],
                            level=zopts['level'],
                            extra_args="")
                    with open(path, 'rb') as f:
                        for chunk in iter(partial(f.read, 4 * 1024), ''):
                            ostream.write(chunk)
                    ostream.close()
                    os.remove(path)

    def info(self):
        """Provide extra information about the backup this plugin produced

        :returns: str. A textual string description the backup referenced by
                       `self.config`
        """
        return "MongoDB using mongodump plugin"
