"""
Tar Backup Plugin
"""

import logging
import os
from subprocess import Popen, list2cmdline
from tempfile import TemporaryFile
from holland.core.backup import BackupError
from holland.lib.compression import open_stream

LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[tar]
directory = string(default='/home')
[compression]
method = option('none', 'gzip', 'gzip-rsyncable', 'pigz', 'bzip2', 'pbzip2', 'lzma', 'lzop', 'gpg', default='gzip')
options = string(default="")
inline = boolean(default=yes)
level  = integer(min=0, max=9, default=1)
""".splitlines()


class TarPlugin(object):
    """
    Define Tar Backup method
    """

    def __init__(self, name, config, target_directory, dry_run=False):
        """Create a new TarPlugin instance

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
        """
        Estimate how large the backup will be
        """
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.config["tar"]["directory"]):
            for files in filenames:
                filepointer = os.path.join(dirpath, files)
                # verify the symlink and such exist before trying to get its size
                if os.path.exists(filepointer):
                    total_size += os.path.getsize(filepointer)
            LOG.debug("Debug: Checking size of %s directories in %s", len(dirnames), dirpath)
        return total_size

    def _open_stream(self, path, mode, method=None):
        """
        Open a stream through the holland compression api, relative to
        this instance's target directory
        """
        compression_method = method or self.config["compression"]["method"]
        compression_level = self.config["compression"]["level"]
        compression_options = self.config["compression"]["options"]
        compression_inline = self.config["compression"]["inline"]
        stream = open_stream(
            path,
            mode,
            compression_method,
            compression_level,
            extra_args=compression_options,
            inline=compression_inline,
        )
        return stream

    def backup(self):
        """
        Create backup
        """
        if self.dry_run:
            return
        if not os.path.exists(self.config["tar"]["directory"]) or not os.path.isdir(
            self.config["tar"]["directory"]
        ):
            raise BackupError("{0} is not a directory!".format(self.config["tar"]["directory"]))
        out_name = "{0}.tar".format(self.config["tar"]["directory"].lstrip("/").replace("/", "_"))
        outfile = os.path.join(self.target_directory, out_name)
        args = ["tar", "c", self.config["tar"]["directory"]]
        errlog = TemporaryFile()
        stream = self._open_stream(outfile, "w")
        LOG.info("Executing: %s", list2cmdline(args))
        pid = Popen(args, stdout=stream.fileno(), stderr=errlog.fileno(), close_fds=True)
        status = pid.wait()
        try:
            errlog.flush()
            errlog.seek(0)
            for line in errlog:
                LOG.error("%s[%d]: %s", list2cmdline(args), pid.pid, line.rstrip())
        finally:
            errlog.close()

        if status != 0:
            raise BackupError("tar failed (status={0})".format(status))
