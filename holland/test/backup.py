"""
holland.test.backup
~~~~~~~~~~~~~~~~~~~

Utilities for testing holland backups

"""

from holland.core import BackupPlugin, BackupError

class TestBackupPlugin(BackupPlugin):
    """A BackupPlugin suitable for testing

    This implementation simply measures the order of events called on the
    plugin class and records them in the instance ``events`` attribute

    If :attr:``die_please`` is set backup() will always raise a BackupError

    """
    die_please = False

    def __init__(self, name):
        super(TestBackupPlugin, self).__init__(name)
        self.events = []

    def setup(self, backupstore):
        """Set the backupstore on the BackupPlugin"""
        super(TestBackupPlugin, self).setup(backupstore)
        self.events.append('setup')

    def configure(self, config):
        """Provide the backup plugin with a configuration"""
        self.events.append('config')

    def estimate(self):
        """Estimate a backup size"""
        return 42

    def pre(self):
        """Run any setup actions"""
        self.events.append('pre')

    def backup(self):
        """Run an actual backup"""
        if self.die_please:
            raise BackupError("Die die die")
        self.events.append('backup')

    def dryrun(self):
        """Perform a dryrun"""
        self.events.append('dryrun')

    def post(self):
        """Perform an post actions"""
        self.events.append('post')

    def release(self):
        """Release any resources held by this plugin"""

    def plugin_info(self):
        "Sample Plugin info"
        return dict(
            name='test',
            author='Holland Core Team',
            summary='A test backup plugin',
            description='''
            This is a backup plugin used for testing.  When called it will
            record the order of methods in a list in the plugin instance events
            attribute.
            ''',
            api_version='1.1.0',
            version='1.1.0'
        )
