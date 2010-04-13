import sys
from types import StringTypes, FileType
import logging
import logging.config

DEFAULT_LEVEL   = logging.NOTSET
DEFAULT_FORMAT  = "%(asctime)s %(name)s %(levelname)s: %(message)s"
DEFAULT_DATEFMT = "%Y-%m-%d %H:%M:%S"

def _convert_strlevel(name):
    level = {
        'CRITICAL' : logging.CRITICAL,
        'ERROR' : logging.ERROR,
        'WARNING' : logging.WARNING,
        'INFO' : logging.INFO,
        'DEBUG' : logging.DEBUG,
    }
    return level.get(name.upper(), logging.WARNING)

def initialize_logging(**kwargs):
    # clear existing root handlers
    root_logger = logging.getLogger()
    map(root_logger.removeHandler, root_logger.handlers)

    # basic setup
    level = kwargs.get('level', DEFAULT_LEVEL)
    if isinstance(level, StringTypes):
        level = _convert_strlevel(level)
    format = kwargs.get('format', DEFAULT_FORMAT)
    datefmt = kwargs.get('datefmt', DEFAULT_DATEFMT)
    output = kwargs.get('output', sys.stderr)
    logging_config = kwargs.get('config_file')

    if logging_config:
        logging.config.fileConfig(logging_config)

    if isinstance(output, StringTypes):
        logging.basicConfig(level=level, format=format, datefmt=datefmt, filename=output)
    elif isinstance(output, FileType):
        logging.basicConfig(level=level, format=format, datefmt=datefmt, stream=output)
    else:
        logging.basicConfig(level=level, format=format, datefmt=datefmt)

def next_loglevel(current_level, increment=1):
    log_levels = [
        logging.CRITICAL,
        logging.ERROR,
        logging.WARNING,
        logging.INFO,
        logging.DEBUG
    ]
    idx = log_levels.index(current_level)
    idx = (idx + increment)
    if idx > len(log_levels):
        idx = len(log_levels) - 1
    return log_levels[idx]

def get_logger():
    return logging.getLogger(__name__)

# Original logging function
def setup_logger(**kwargs):
    verbose = kwargs.get("stdout_verbose", False)
    filename = kwargs.get("log_filename", "/var/log/holland/holland.log")
    max_size = kwargs.get("log_max_size", 1073741824)
    keep_count = kwargs.get("log_backup_count", 4)

    log_dir = os.path.dirname(filename)
    h.ensure_dir(log_dir)

    log = h.get_logger('holland')

    # See if there is a bootstrap handler and remove it
    if len(log.handlers) == 1:
        if hasattr(log.handlers[0], "name"):
            if log.handlers[0].name == "bootstrap":
                log.removeHandler(log.handlers[0])

    logging = h.get_logging()
    log.setLevel(logging.DEBUG)

    console = logging.StreamHandler()
    if verbose:
        console.setLevel(logging.DEBUG)
    else:
        console.setLevel(logging.INFO)

    file = logging.handlers.RotatingFileHandler(filename=filename,
                                                maxBytes=max_size,
                                                backupCount=keep_count)
    file.setLevel(logging.DEBUG)
    cformatter = logging.Formatter("%(levelname)-8s:  %(message)s")
    fformatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s: %(message)s")

    console.setFormatter(cformatter)
    file.setFormatter(fformatter)

    log.addHandler(console)
    log.addHandler(file)
