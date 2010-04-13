import unittest, doctest

import test_ini
import test_misc
import test_fuzz
import test_compat
import test_unicode
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
