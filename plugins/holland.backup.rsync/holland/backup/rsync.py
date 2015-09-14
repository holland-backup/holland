import logging
import os
from subprocess import Popen, PIPE, STDOUT, list2cmdline
from holland.core.exceptions import BackupError
from tempfile import TemporaryFile

LOG = logging.getLogger(__name__)

# Specification for this plugin
# See: http://www.voidspace.org.uk/python/validate.html
CONFIGSPEC = """
[rsync]
directory = string(default='/home')
hardlinks = boolean(default=yes)
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
		if self.dry_run:
			return

		#if not os.path.exists(self.config['rsync']['directory'])
		#or not os.path.isdir(self.config['rsync']['directory']):
		#	raise BackupError('{0} is not a directory!'.format(self.config['rsync']['directory']))
		outdir = os.path.join(self.target_directory, self.config['rsync']['directory'])
		cmd = ['rsync', '-avz', self.config['rsync']['directory'], outdir]
		errlog = TemporaryFile()
		#stream = self._open_stream(outfile, 'w')
		LOG.info("Executing: %s", list2cmdline(cmd))
		pid = Popen(
			cmd,
			#stdout=stream.fileno(),
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
