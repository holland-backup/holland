import os
import sys
import logging
from options import build_option_parser
from ConfigParser import RawConfigParser as _ConfigParser
from holland.backup.lvm.core import mysql_snapshot_lifecycle

def load_config(path):
    _ConfigParser.optionxform = lambda self, key: key.replace('-', '_')
    cfg = _ConfigParser()
    cfg.read([path])
    return dict(sum(map(cfg.items, cfg.sections()), []))

def start(args=None):
    logging.basicConfig(level=logging.DEBUG)
    parser = build_option_parser()
    ns = parser.parse_args()

    if not ns.backup_file:
        parser.error("Please specify a file to archive to.")

    cfg = load_config(ns.config)
    # Merge config-line options
    cfg.update(ns.__dict__)

    # Set defaults
    for key, value in parser._defaults.items():
        if key not in cfg:
            cfg[key] = value

    fsm = mysql_snapshot_lifecycle(innodb_recovery=ns.innodb_recovery)
    fsm.run()

    return os.EX_OK

#if __name__ == '__main__':
#    sys.exit(main())
