"""
holland.backup.random
~~~~~~~~~~~~~~~~~~~~~

Backup bytes from /dev/urandom

This plugin is an example of how to write a holland backup plugin

"""

import os
import logging
from holland.core import Configspec, BackupPlugin, BackupError
LOG = logging.getLogger(__name__)

class RandomPlugin(BackupPlugin):
    """Back up randomness"""

    def estimate(self):
        return self.config['random']['bytes']

    def backup(self):
        rand = open("/dev/urandom", "r")
        bytesleft = self.config['random']['bytes']
        data = ''
        while bytesleft > 0:
            r = rand.read(bytesleft)
            data += r
            bytesleft -= len(r)
            LOG.info("Read %d bytes from /dev/urandom" % len(r))

        # backup_directory is automatically configured for us by
        # the holland backup API
        outfile = os.path.join(self.backup_directory, 'random_data')

        # be sure to catch errors and raise a BackupErrora
        try:
            f = open(outfile, "w")
            f.write(data)
            f.close()
            LOG.info("Wrote to "+outfile)
        except IOError, exc:
            raise BackupError("Failed to backup /dev/urandom: %s" % exc)

    def dryrun(self):
        LOG.info(" * Would read %d bytes from /dev/urandom",
                 self.config['random']['bytes'])

    def configspec(self):
        return Configspec.from_string('''
        [random]
        bytes = integer(default=50)
        ''')

    def plugin_info(self):
        return dict(
            name='random',
            author='Rackspace',
            summary='A plugin that backups up /dev/urandom',
            description='''
            This plugin reads a defined number of bytes from /dev/urandom and
            saves these to a backup file called 'random_data' in the
            backup directory.

            This is just an example to demonstrate the structure and functionality
            of a holland backup plugin.
            ''',
            version='1.1',
            api_version='1.1.0'
        )
