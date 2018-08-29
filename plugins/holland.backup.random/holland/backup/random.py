"""
Create Class to backup random data
"""

import logging
import os
LOG = logging.getLogger(__name__)

CONFIGSPEC = """
[random]
bytes = integer(default=50)
""".splitlines()

class RandomPlugin(object):
    """Back up randomness"""
    def __init__(self, name, config, target_directory, dry_run=False):
        """Create new RandomPlugin instance"""

        self.name = name
        self.config = config
        self.target_directory = target_directory
        self.dry_run = dry_run
        LOG.info("Validating Config")
        self.config.validate_config(CONFIGSPEC)
        self.bytes = self.config['random']['bytes']

    def estimate_backup_size(self):
        """Return estimated backup size"""
        return self.bytes

    def backup(self):
        """Backup data from /dev/random"""
        rand = open("/dev/random", "r")
        bytesleft = self.bytes
        data = ''
        while bytesleft > 0:
            random = rand.read(bytesleft)
            data += random
            bytesleft -= len(random)
            LOG.info("Read %d bytes from /dev/random", len(random))

        outfile = os.path.join(self.target_directory, 'random_data')
        filehandle = open(outfile, "w")
        filehandle.write(data)
        filehandle.close()
        LOG.info("Wrote to " + outfile)
