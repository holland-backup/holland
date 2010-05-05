import os, sys
import shlex, subprocess
import shutil
import ConfigParser

# Functions
def execute(cmd, config):
    returnCode = subprocess.call(cmd, 
        stdout=config.get('global', 'output_log'), 
        stderr=config.get('global', 'error_log'))
    if returnCode != 0:
        print "Failure is not an option! Except when it is"
        sys.exit(returnCode)
    return

# Setup
pwd = os.getcwd()
config = ConfigParser.ConfigParser()
config.read('test.conf')
outputLog = open('results/output.log', 'w')
errorLog = open('results/error.log', 'w')

# Create a sandbox

subprocess.call([
    'make_sandbox', 
    config.get('sandbox','tarball'),
    '--upper_directory=' + config.get('sandbox','upper_directory'),
    '--sandbox_directory=' + config.get('sandbox','sandbox_directory'),
    '--datadir_from=' + config.get('sandbox', 'datadir_from'),
    '--sandbox_port=' + config.get('sandbox', 'port'),
    '--db_user=' + config.get('sandbox', 'user'),
    '--db_password=' + config.get('sandbox', 'password'),
    '--no_confirm'
    ], 
    stdout=outputLog,
    stderr=errorLog)

# Setup Holland virtual environment
if not(os.path.exists(config.get('global', 'holland_install_dir'))):
    os.mkdir(config.get('global', 'holland_install_dir'))

holland_path = pwd + '/' + config.get('global', 'holland_install_dir')
status = subprocess.call(['virtualenv', holland_path]) 
os.environ['PATH'] = os.path.join(holland_path, 'bin') + ':' + os.environ['PATH']
subprocess.call(['python', 'setup.py', 'install'],
    cwd=config.get('global', 'holland_repository'),
    stdout=outputLog,
    stderr=errorLog)

plugin_dir=config.get('global', 'holland_repository') + '/plugins'
for plugin in open(plugin_dir + '/ACTIVE', 'r'):
    subprocess.call(['python', 'setup.py', 'install'], 
        cwd=plugin_dir + '/' + plugin.strip(),
        stdout=outputLog,
        stderr=errorLog)

# Copy Config Files
if not(os.path.exists(config.get('global', 'holland_install_dir') + '/etc')):
    os.mkdir(config.get('global', 'holland_install_dir') + '/etc')
shutil.copytree(
    config.get('global', 'holland_config_dir'), 
    config.get('global', 'holland_install_dir') + '/etc/holland')

# Back some shit up, w00!
holland_path = pwd + '/' + config.get('global', 'holland_install_dir')
status = subprocess.call(['virtualenv', holland_path])
subprocess.call([
    'holland', 
    '--config-file=' + config.get('global', 'holland_config_dir'), 
    'bk'],
    cwd=config.get('global', 'holland_repository'),
    shell=True)

# Cleanup
subprocess.call([pwd + '/sandbox/mysql/stop'], shell=True)
shutil.rmtree(pwd + '/sandbox/mysql')
shutil.rmtree(pwd + '/' + config.get('global', 'holland_install_dir'))
