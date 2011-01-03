import sys

if sys.version_info < (3, 0):
    import argparse
    import subprocess
    import logging
    from logging import handlers as logging_handlers
    from logging import config as logging_config
    import configobj
    import validate

def setup_backports():
    if sys.version_info < (3, 0):
        module_list = [
            'argparse',
            'subprocess',
            'logging',
            'configobj',
            'validate',
        ]
        for module in module_list:
            sys.modules[module] = globals()[module]
        sys.modules['logging.handlers'] = logging_handlers
        sys.modules['logging.config'] = logging_config
