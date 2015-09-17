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
password = string(default=None)
directory = string(default='/')
flags = string(default='-avz')
hardlinks = boolean(default=yes)
one-file-system = boolean(default=no)
exclude = list(default=None)
bandwidth-limit = string(default=None)
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
		# This is 0 for now because estimating size for very large directories
		# could be super time consuming and may not even be accurate if
		# one-file-system is used. Another method other than what is below
		# may need to be used instead.
		return 0
		#total_size = 0
		#for dirpath, dirnames, filenames in os.walk(self.config['rsync']['directory']):
		#	for f in filenames:
		#		fp = os.path.join(dirpath, f)
		#		# verify the symlink and such exist before trying to get its size
		#		if os.path.exists(fp):
		#			total_size += os.path.getsize(fp)
		#return total_size

	def backup(self):
		hardlink_cmd = ""
		env = None

		if self.dry_run:
			return

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

			# Now we build the --rsh flag

			#if(self.config['rsync']['port']):
				#rsh = "--rsh='ssh"
				#rsh += " -p"
				#-p" #+ str(self.config['rsync']['port']) + "'"
				#LOG.info(rsh)
				#cmd.append(rsh)
			#else:
				#rsh="""--rsh='ssh'"""
			#cmd.append(rsh)

		# Now concatenate all the above work with the desired path.
		source += "/" + self.config['rsync']['directory']

		# Check on the bandwidth limit
		if(self.config['rsync']['bandwidth-limit']):
			cmd.append('--bwlimit=' + self.config['rsync']['bandwidth-limit'])

		# Check on one-file-system flag
		if(self.config['rsync']['one-file-system']):
			cmd.append('--one-file-system')

		# Append the source and destinations
		cmd.append(source)
		cmd.append(self.target_directory)

		# Do it!
		errlog = TemporaryFile()
		LOG.info("Executing: %s", list2cmdline(cmd))
		pid = Popen(
			cmd,
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
			errlog.close()
