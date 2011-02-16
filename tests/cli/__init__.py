import sys

def setup():
    import holland.cli.backports.argparse as argparse

    sys.modules['argparse'] = argparse
