import sys
import holland.core.backports.logging
import holland.core.backports.logging.config
import holland.core.backports.logging.handlers
import holland.core.backports.optparse
import holland.core.backports.subprocess
import holland.core.backports.zipfile

# TODO: Should these be conditionally loaded?
sys.modules['logging'] = logging
sys.modules['logging.config'] = logging.config
sys.modules['logging.handlers'] = logging.handlers
sys.modules['optparse'] = optparse
sys.modules['subprocess'] = subprocess
sys.modules['zipfile'] = zipfile
