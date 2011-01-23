import sys

if sys.version_info < (3, 0):
    import argparse
    import subprocess

def setup_backports():
    if sys.version_info < (3, 0):
        module_list = [
            'argparse',
            'subprocess',
        ]
        for module in module_list:
            sys.modules[module] = globals()[module]
