from holland.core import BackupPlugin, BackupError

class TestBackupPlugin(BackupPlugin):
    die_please = False

    def __init__(self, name):
        self.name = name
        self.events = []

    def setup(self, backupstore):
        self.events.append('setup')

    def configure(self, config):
        self.events.append('config')

    def estimate(self):
        return 42

    def pre(self):
        self.events.append('pre')

    def backup(self):
        if self.die_please:
            raise BackupError("Die die die")
        self.events.append('backup')

    def dryrun(self):
        self.events.append('dryrun')

    def post(self):
        self.events.append('post')

    def cleanup(self):
        "cleanup after a backup run"

    def plugin_info(self):
        "Sample Plugin info"
        return dict(
            name='test',
            author='Andrew Garner',
            api_version='1.1.0',
            version='1.0'
        )
