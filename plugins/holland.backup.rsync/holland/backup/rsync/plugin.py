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
method = option('local', 'ssh', 'rsync', default='local')
server = string(default=None)
port = integer(default=None)
username = string(default=None)
keyfile = string(default=None)
password = string(default=None)
directory = string(default='/')
flags = string(default='-avz')
hardlinks = boolean(default=yes)
one-file-system = boolean(default=no)
bandwidth-limit = string(default=None)
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
		# We return None because estimating size for very large directories
		# could be super time consuming and may not even be accurate if
		# one-file-system is used, and that's just for local rsync's.
		# Remote rsyncs would require comparing the output of a --dry-run.
		# All options seem to be expensive so this is a topic for another day.
		return None

	def backup(self):
		env = None

		# Check if the directory we are trying to backup exists
		# if we are backing up a local directory.
		if self.config['rsync']['method'] == 'local':
			if not os.path.exists(self.config['rsync']['directory']):
				raise BackupError('{0} does not exist!'.format(self.config['rsync']['directory']))
			if not os.path.isdir(self.config['rsync']['directory']):
				raise BackupError('{0} is not a directory!'.format(self.config['rsync']['directory']))

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

		# Check the rsync method (local, ssh, rsync)
		# Each case, we're doing local copy so we do nothing.
		if(self.config['rsync']['method'] == 'local'):
			source = ""
		# We're using rsync. If a username was specified, provide it.
		elif(self.config['rsync']['method'] == 'rsync'):
			source = "rsync://"
			if(self.config['rsync']['username']):
				source += self.config['rsync']['username'] + "@"
			# Add in the host
			source += self.config['rsync']['server']
			# If a port was specified, provide it as well.
			if(self.config['rsync']['port']):
				source += ":" + self.config['rsync']['port']
			# If a password was specified, toss it in as a env variable.
			if(self.config['rsync']['password']):
				env = {"RSYNC_PASSWORD": self.config['rsync']['password']}

		# We're using SSH. If a username was specified, provide it.
		# Note no password will be provided here. SSH keys should be used.
		# The "user@host:/path" syntax is being used here.
		elif(self.config['rsync']['method'] == 'ssh'):
			source = ""
			if(self.config['rsync']['username']):
				source = self.config['rsync']['username'] + "@"
			source += self.config['rsync']['server'] + ":"

			# Now we build the SSH sub-command
			# This is a bit ugly, in part due to how subprocess
			# likes to parse command-line arguments.
			if(self.config['rsync']['port']
				or self.config['rsync']['keyfile']):
				port = ""
				key = ""
				if(self.config['rsync']['port']):
					port = "-p%s" % str(self.config['rsync']['port'])
				if(self.config['rsync']['keyfile']):
					key = "-i%s" % self.config['rsync']['keyfile']
				cmd.append('-e')
				cmd.append("ssh -o PasswordAuthentication=false %s %s" % (port, key))

		# Now concatenate all the above work with the desired path.
		source += "/" + self.config['rsync']['directory']

		# Check on the bandwidth limit
		if(self.config['rsync']['bandwidth-limit']):
			cmd.append('--bwlimit=' + self.config['rsync']['bandwidth-limit'])

		# Check on one-file-system flag
		if(self.config['rsync']['one-file-system']):
			cmd.append('--one-file-system')

		# If using Holland's --dry-run, add rsync's --dry-run
		# and redirect rsync's output to stdout.
		if self.dry_run:
			cmd.append('--dry-run')
			output = None
		else:
			output = open(self.target_directory + "/output.txt", 'w')

		# Append the source and destinations
		cmd.append(source)
		cmd.append(self.target_directory)

		# Do it!
		errlog = TemporaryFile()
		LOG.info("Executing: %s", list2cmdline(cmd))
		pid = Popen(
			cmd,
			stdout=output,
			stderr=errlog.fileno(),
			env=env,
			close_fds=True)
		status = pid.wait()
		try:
			errlog.flush()
			errlog.seek(0)
			for line in errlog:
				LOG.error("%s[%d]: %s", list2cmdline(cmd), pid.pid, line.rstrip())
		finally:
			if not self.dry_run:
				output.close()
			errlog.close()
