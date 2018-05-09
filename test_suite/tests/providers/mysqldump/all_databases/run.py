import os, sys
import shlex, subprocess
import shutil
import configparser

# Functions
def execute(cmd, config):
    returnCode = subprocess.call(cmd, 
        stdout=config.get('global', 'output_log'), 
        stderr=config.get('global', 'error_log'))
    if returnCode != 0:
        print("Failure is not an option! Except when it is")
        sys.exit(returnCode)
    return

# Setup
pwd = os.getcwd()
config = configparser.ConfigParser()
config.read('config/test.conf')
outputLog = open(config.get('global', 'output_log'), 'w')
errorLog = open(config.get('global', 'error_log'), 'w')

# Create a sandbox
subprocess.call([
    'make_sandbox', 
    config.get('sandbox','tarball'),
    '--upper_directory=' + pwd + '/' + config.get('sandbox','upper_directory'),
    '--sandbox_directory=' + config.get('sandbox','sandbox_directory'),
    '--datadir_from=' + config.get('sandbox', 'datadir_from'),
    '--sandbox_port=' + config.get('sandbox', 'port'),
    '--db_user=' + config.get('sandbox', 'user'),
    '--db_password=' + config.get('sandbox', 'password'),
    '--no_confirm'
    ], 
    stdout=outputLog,
    stderr=errorLog)
subprocess.call([pwd + '/sandbox/mysql/start'], stdout=outputLog, stderr=errorLog)

# Run Maatkit before backup
maatkit_output = open('results/before-restore.mkt', 'w')
subprocess.call(shlex.split('mk-table-checksum localhost' +
    ' --port=' + config.get('sandbox', 'port') +
    ' --user=' + config.get('sandbox', 'user') +
    ' --password=' + config.get('sandbox', 'password')),
    stdout=maatkit_output,
    stderr=errorLog)
maatkit_output.close()

# Setup Holland virtual environment
if not os.path.exists(config.get('global', 'holland_install_dir')):
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
running_config_dir=config.get('global', 'holland_install_dir') + '/etc/holland'
if not os.path.exists(config.get('global', 'holland_install_dir') + '/etc'):
    os.mkdir(config.get('global', 'holland_install_dir') + '/etc')
if not os.path.exists(config.get('global', 'holland_install_dir') + '/etc/holland'):
    os.mkdir(config.get('global', 'holland_install_dir') + '/etc/holland')
shutil.copytree(
    config.get('global', 'backupset_config_dir'),
    running_config_dir + '/backupsets')
shutil.copytree(
    config.get('global', 'provider_config_dir'),
    running_config_dir + '/providers')

# Generate holland.conf from main test config
holland_config = configparser.ConfigParser()
holland_config.add_section('holland')
for item, value in config.items('holland'):
    holland_config.set('holland', item, value)
holland_config_file = open(running_config_dir + '/holland.conf', 'w')
holland_config.write(holland_config_file)
holland_config_file.close()

# Back some shit up, w00!
holland_path = pwd + '/' + config.get('global', 'holland_install_dir')
subprocess.call(['virtualenv', holland_path])
subprocess.call(shlex.split(
    'bin/holland --config-file=' + 
    'etc/holland/holland.conf bk'),
    cwd=holland_path)



# Cleanup
subprocess.call([pwd + '/sandbox/mysql/stop'])
shutil.rmtree(pwd + '/sandbox/mysql')
shutil.rmtree(pwd + '/' + config.get('global', 'holland_install_dir'))
outputLog.close() 
errorLog.close()

