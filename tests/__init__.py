#
import os
from pkg_resources import *

def setup():
    """Pull in the main holland egg into pkg_resources"""
    path = os.path.dirname(os.path.dirname(__file__))
    env = Environment([path])
    dists, errors = working_set.find_plugins(env)
    for dist in dists:
        working_set.add(dist)

    # setup logging
    import logging
    class NullHandler(logging.Handler):
            def emit(self, record):
                pass
    logging.getLogger("holland").addHandler(NullHandler())
