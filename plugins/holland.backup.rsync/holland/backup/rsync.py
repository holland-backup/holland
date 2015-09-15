import logging
import os
from subprocess import Popen, PIPE, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from holland.core import spool
from holland.core import config
from tempfile import TemporaryFile

LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[rsync]
directory = string(default='/home')
flags = string(default='-avz')
hardlinks = boolean(default=yes)
exclude = list(default=None)
""".splitlines()

class RsyncPlugin(object):
	def __init__(self, name, config, target_directory, dry_run=False):
		"""Create a new RsyncPlugin instance

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
		total_size = 0
		for dirpath, dirnames, filenames in os.walk(self.config['rsync']['directory']):
			for f in filenames:
				fp = os.path.join(dirpath, f)
				# verify the symlink and such exist before trying to get its size
				if os.path.exists(fp):
					total_size += os.path.getsize(fp)
		return total_size

	def backup(self):
		hardlink_cmd = ""

		if self.dry_run:
			return

		# Check if the directory we are trying to backup exists
		if not os.path.exists(self.config['rsync']['directory']):
			raise BackupError('{0} does not exist!'.format(self.config['rsync']['directory']))
		if not os.path.isdir(self.config['rsync']['directory']):
			raise BackupError('{0} is not a directory!'.format(self.config['rsync']['directory']))

		# Process exclusion tuples and turn them into
		# --exclude flags
		if self.config['rsync']['exclude']:
			for exclude in self.config['rsync']['exclude']:
				excludes.append("--exclude=" + exclude)


		# Check if a previous backup directory exists
		# if so, and hardlinks are enabled, use it for the --link-dest
		self.spool = spool.Spool()
		backupsets = self.spool.find_backupset(self.name)
		backups = backupsets.list_backups(reverse=True)
		if len(backups) > 1 and self.config['rsync']['hardlinks']:
			LOG.info("Previous Backup Found: %s", backups[1].path)
			cmd = ['rsync', self.config['rsync']['flags'], "--link-dest=" + backups[1].path]
		else:
			cmd = ['rsync', self.config['rsync']['flags']]

		# Process exclusion tuples and turn them into
		# --exclude flags
		if self.config['rsync']['exclude']:
			for exclude in self.config['rsync']['exclude']:
				cmd.append("--exclude=" + exclude)

		# Append the source and destinations
		cmd.append(self.config['rsync']['directory'])
		cmd.append(self.target_directory)

		# Do it!
		errlog = TemporaryFile()
		LOG.info("Executing: %s", list2cmdline(cmd))
		pid = Popen(
			cmd,
			stderr=errlog.fileno(),
			close_fds=True)
		status = pid.wait()
		try:
			errlog.flush()
			errlog.seek(0)
			for line in errlog:
				LOG.error("%s[%d]: %s", list2cmdline(cmd), pid.pid, line.rstrip())
		finally:
			errlog.close()
