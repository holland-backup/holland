"""Proform backup of MongoDB database"""

import logging
import os
import os.path
import subprocess
import urllib
from io import open  # pylint: disable=redefined-builtin

from pymongo import MongoClient

from holland.core.backup import BackupError
from holland.lib.compression import COMPRESSION_CONFIG_STRING, open_stream
from holland.lib.which import which

LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = (
    """
[mongodump]
host = string(default=None)
username = string(default=None)
password = string(default=None)
authenticationDatabase = string(default=None)
uri = force_list(default=list())
additional-options = force_list(default=list())
"""
    + COMPRESSION_CONFIG_STRING
)

CONFIGSPEC = CONFIGSPEC.splitlines()


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

        uri = self.config["mongodump"].get("uri")
        if uri and uri != [""]:
            uri = ",".join(uri)
        else:
            uri = "mongodb://"
            username = self.config["mongodump"].get("username")
            if username:
                uri += urllib.parse.quote_plus(username)
                password = self.config["mongodump"].get("password")
                if password:
                    uri += ":" + urllib.parse.quote_plus(password)
                uri += "@"
            uri += self.config["mongodump"].get("host")
        client = MongoClient(uri)
        dbs = client.database_names()
        for database in dbs:
            c_db = client[database]
            tup = c_db.command("dbstats")
            ret += int(tup["storageSize"])
        # Give an upper estimate to make sure that we have enough disk space
        return ret * 2

    def backup(self):
        """
        Do what is necessary to perform and validate a successful backup.
        """
        command = [which("mongodump")]
        uri = self.config["mongodump"].get("uri")
        if uri and uri != [""]:
            command.extend(["--uri", ",".join(uri)])
        else:
            username = self.config["mongodump"].get("username")
            if username:
                command += ["-u", username]
                password = self.config["mongodump"].get("password")
                if password:
                    command += ["-p", password]
            command += ["--host", self.config["mongodump"].get("host")]
        command += ["--out", self.target_directory]
        add_options = self.config["mongodump"].get("additional-options")
        if add_options:
            command.extend(add_options)

        if self.dry_run:
            LOG.info("[Dry run] MongoDump Plugin - test backup run")
            LOG.info("MongoDump command: %s", subprocess.list2cmdline(command))
        else:
            LOG.info("MongoDump command: %s", subprocess.list2cmdline(command))
            logfile = open(os.path.join(self.target_directory, "mongodump.log"), "w")
            proc = subprocess.Popen(command, stdout=logfile, stderr=logfile)
            ret = proc.wait()

            if ret != 0:
                raise BackupError("Mongodump returned %d" % ret)
            for root, _, files in os.walk(self.target_directory):
                for file_object in files:
                    if ".log" in file_object or ".conf" in file_object:
                        continue
                    if ".gz" in file_object:
                        continue
                    path = os.path.join(root, file_object)
                    LOG.info("Compressing file %s", path)
                    ostream = open_stream(path, "w", **self.config["compression"])
                    with open(path, "rb") as file_object:
                        ostream.write(file_object.read())
                    ostream.close()
                    os.remove(path)

    @staticmethod
    def info():
        """Provide extra information about the backup this plugin produced

        :returns: str. A textual string description the backup referenced by
                       `self.config`
        """
        return "MongoDB using mongodump plugin"
