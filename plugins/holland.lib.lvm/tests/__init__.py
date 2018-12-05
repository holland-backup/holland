# pylint: skip-file

import sys
import os, sys
import shutil
import tempfile
import subprocess
from nose.tools import *
from holland.lib.lvm.raw import *
from tests.constants import *

def teardown():
    shutil.rmtree(MNT_DIR)
