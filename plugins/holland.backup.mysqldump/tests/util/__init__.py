# pylint: skip-file

import unittest, doctest

from . import test_ini
from . import test_misc
from . import test_fuzz
from . import test_compat
from . import test_unicode
from holland.backup.mysqldump.util import config
from holland.backup.mysqldump.util import ini

class suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
                doctest.DocTestSuite(config),
                doctest.DocTestSuite(ini),
                test_ini.suite(),
                test_misc.suite(),
                test_fuzz.suite(),
                test_compat.suite(),
                test_unicode.suite(),
        ])
