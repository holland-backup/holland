import re
import logging
from subprocess import Popen, PIPE, list2cmdline
from exc import BackupError

def mysqldump_args(databases, defaults_file, extra_options):
    argv = [
        'mysqldump',
    ]

    if defaults_file:
        argv.append('--defaults-file=%s' % defaults_file)

    if extra_options:
        argv.extend(extra_options)

    argv.append('--databases')
    argv.extend(databases)

    return argv

def mysqldump(result_file,
              databases=None,
              defaults_file=None,
              extra_options=None):
    validate_extra_options(extra_options)
    collapse_extra_options(extra_options)
    args = mysqldump_args(databases, defaults_file, extra_options)
    logging.info("%s", list2cmdline(args))
    pid = Popen(args,
                stdout=result_file.fileno(),
                stderr=PIPE,
                close_fds=True)
    while pid.poll() is None:
        line = pid.stderr.readline()
        if not line:
            # eof
            break
        logging.error("[mysqldump:error] %s", line.rstrip())
    pid.wait()
    logging.info("mysqldump finished")
    if pid.returncode != 0:
        logging.debug("pid.returncode = %r", pid.returncode)
        raise BackupError("mysqldump failure[%d]" % pid.returncode)


def validate_extra_options(mysqldump_options):
    if not mysqldump_options:
        return

    for opt in mysqldump_options:
        validate_one_option(opt)

def collapse_extra_options(options):
    result = []
    for opt in options:
        if opt in result:
            logging.warning("Removing duplicate option %r", opt)
        else:
            result.append(opt)
    del options[:]
    options.extend(result)

# map patterns to actions
# passthrough => OK
# raise UnsupportedOption => not support by us
# raise InvalidOption => Not supported by mysqldump
def validate_one_option(opt):
    valid_options = [
        r'--flush-logs$',
        r'--routines$',
        r'--events$',
        r'--single-transaction$',
        r'--lock-all-tables$',
        r'--lock-tables$',
        r'--default-character-set=\w+$',
        r'--master-data(=\d)?$',
        r'--flush-privileges$'
    ]

    for opt_check in valid_options:
        if re.match(opt_check, opt):
            break
        logging.debug("%r did not match %r", opt, opt_check)
    else:
        raise BackupError("Invalid option %s" % opt)
