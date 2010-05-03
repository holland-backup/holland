import os, sys
import shlex, subprocess
import shutil
import ConfigParser

pwd = os.getcwd()

config = ConfigParser.ConfigParser()
config.read('test.conf')

# Create Sandbox
sandboxLog = open('results/sandbox.log', 'w')
proc = subprocess.Popen([
    'make_sandbox', 
    config.get('sandbox','tarball'),
    '--upper_directory=' + config.get('sandbox','upper_directory'),
    '--sandbox_directory=' + config.get('sandbox','sandbox_directory'),
    '--datadir_from=' + config.get('sandbox', 'datadir_from'),
    '--sandbox_port=' + config.get('sandbox', 'port'),
    '--db_user=' + config.get('sandbox', 'user'),
    '--db_password=' + config.get('sandbox', 'password'),
    '--no_confirm'
], 0, None, sandboxLog, sandboxLog)
proc.communicate()

# Cleanup
subprocess.Popen([pwd + '/sandbox/mysql/stop'], shell=True)
shutil.rmtree(pwd + '/sandbox/mysql')
