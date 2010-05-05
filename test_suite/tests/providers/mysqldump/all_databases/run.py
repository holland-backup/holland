import os, sys
import shlex, subprocess
import shutil
import ConfigParser

# Functions
def execute(config, cmd):
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

# Create Sandbox
outputLog = open('results/output.log', 'w')
errorLog = open('results/error.log', 'w')
execute([
    'make_sandbox', 
    config.get('sandbox','tarball'),
    '--upper_directory=' + config.get('sandbox','upper_directory'),
    '--sandbox_directory=' + config.get('sandbox','sandbox_directory'),
    '--datadir_from=' + config.get('sandbox', 'datadir_from'),
    '--sandbox_port=' + config.get('sandbox', 'port'),
    '--db_user=' + config.get('sandbox', 'user'),
    '--db_password=' + config.get('sandbox', 'password'),
    '--no_confirm'
])
"""
# Setup Holland virtual environment
if not(os.path.exists(config.get('global', 'holland_install_dir'))):
    os.mkdir(config.get('global', 'holland_install_dir'))
path = pwd + '/' + config.get('global', 'holland_install_dir')
status = subprocess.call(['virtualenv', path]) 
os.environ['PATH'] = os.path.join(path, 'bin') + ':' + os.environ['PATH']
subprocess.call(['python', 'setup.py', 'install'],
    cwd=config.get('global', 'holland_repository'))

for plugin in open(config.get('global', 'holland_repository') + '/plugins/ACTIVE', 'r'):
    print plugin

# Cleanup
subprocess.call([pwd + '/sandbox/mysql/stop'], shell=True)
shutil.rmtree(pwd + '/sandbox/mysql')
shutil.rmtree(pwd + '/' + config.get('global', 'holland_install_dir')
"""
