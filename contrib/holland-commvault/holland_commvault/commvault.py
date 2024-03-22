"""
Commvault command entry point

The janky arguments Commvault throws at us
http://documentation.commvault.com/commvault/release_8_0_0/books_online_1/english_us/features/pre_post/prepost_process.htm
http://documentation.commvault.com/commvault/release_7_0_0/books_online_1/english_us/features/pre_post/prepost_process.htm
CV_ARGS = ("-bkplevel",
           "-attempt",
           "-status",
           "-job",
           "-vm"
           "-cn")
"""

import logging
import os
import resource
import sys
from argparse import Action, ArgumentParser
from time import sleep

from holland.core.cmdshell import HOLLAND_VERSION
from holland.core.command import run
from holland.core.config.config import HOLLANDCFG
from holland.core.util.bootstrap import bootstrap
from holland.core.util.fmt import format_loglevel

try:
    from pid import PidFile, PidFileAlreadyLockedError

    ENABLE_PID = True
except ImportError:
    ENABLE_PID = False


class ArgList(Action):
    """
    Setup arg list
    """

    def __call__(self, parser, namespace, value, option_string=None):
        arg_list = [x.strip() for x in value.split(",")]
        setattr(namespace, self.dest, arg_list)


def main():
    """
    For some reason (take a wild guess) Commvault has decided that
    their long options will take the form of '-option' not the standard
    '--option'.


    Always set HOME to '/root', as the commvault environment is bare
    """
    os.environ["HOME"] = "/root"
    os.environ["TMPDIR"] = "/tmp"
    # ensure we do not inherit commvault's LD_LIBRARY_PATH
    os.environ.pop("LD_LIBRARY_PATH", None)

    holland_conf = "/etc/holland/holland.conf"
    if sys.platform.startswith("freebsd"):
        holland_conf = "/usr/local" + holland_conf

    parser = ArgumentParser()
    parser.add_argument(
        "--config-file", "-c", metavar="<file>", help="Read configuration from the given file"
    )

    parser.add_argument(
        "-l",
        "--log-level",
        metavar="<log-level>",
        choices=["critical", "error", "warning", "info", "debug"],
        help="Specify the log level. " "One of: critical,error,warning,info,debug",
    )
    parser.add_argument("--quiet", "-q", action="store_true", help="Don't log to console")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument(
        "--bksets",
        "-b",
        metavar="<bkset>,<bkset>...",
        help="only run the specified backupset",
        default=[],
        action=ArgList,
    )

    parser.add_argument("-bkplevel", type=int)
    parser.add_argument("-attempt", type=int)
    parser.add_argument("-status", type=int)
    parser.add_argument("-job", type=int)
    parser.add_argument("-vm")
    parser.add_argument("-cn")
    parser.set_defaults(config_file=os.getenv("HOLLAND_CONFIG") or holland_conf, verbose=False)

    args, largs = parser.parse_known_args(sys.argv[1:])
    if args.log_level:
        args.log_level = format_loglevel(args.log_level)

    bootstrap(args)

    logging.info("Holland (commvault agent) %s started with pid %d", HOLLAND_VERSION, os.getpid())
    # Commvault usually runs with a very low default limit for nofile
    # so a best effort is taken to raise that here.
    try:
        resource.setrlimit(resource.RLIMIT_NOFILE, (262144, 262144))
        logging.debug("(Adjusted ulimit -n (RLIMIT_NOFILE) to %d)", 262144)
    except (ValueError, resource.error) as exc:
        logging.debug("Failed to raise RLIMIT_NOFILE: %s", exc)

    args.command = "backup"
    args.dry_run = 0
    args.no_lock = 0
    spool = HOLLANDCFG.lookup("holland.backup-directory")
    if not args.bksets:
        largs = HOLLANDCFG.lookup("holland.backupsets")
    else:
        largs = args.bksets

    if not ENABLE_PID:
        if run(args, largs):
            return 1
        return 0

    # Use PID module to drop a status file
    status_file = "%s/%s/newest/job_%s" % (spool, largs[0], args.job)
    logging.info("status_file: %s", status_file)
    pid_name = "holland_commvault_%s" % args.job
    pid_location = "/var/run/%s.pid" % pid_name
    try:
        with PidFile(pid_name):
            ret = 0
            if run(args, largs):
                ret = 1
            status = open(status_file, "w")
            status.write(str(ret))
            status.close()
            return ret
    except PidFileAlreadyLockedError:
        pid_file = open(pid_location, "r")
        pid = pid_file.read()
        pid_file.close()

        logging.info("Holland (commvault agent) is already running, waiting for the pid %s", pid)
        count = 0
        while os.path.isfile(pid_location):
            sleep(10)
            count = count + 1
            # ~14 hour timeout
            if count > 5040:
                logging.info("Holland (commvault agent) timed out after %s seconds", count * 10)
                return 1
        try:
            status = open(status_file, "r")
            ret = int(status.read())
        except IOError:
            logging.info("Holland (commvault agent) failed to open/read status file")
            return 1
        status.close()
        return ret
    except IOError as ex:
        logging.warning("Holland (commvault agent) IOError: %r", ex)
        return 1
