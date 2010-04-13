import unittest
from StringIO import StringIO
from holland.backup.mysqldump.util import compat, ini

class test_unicode(unittest.TestCase):
    """Test files read in unicode-mode."""

    s1 = u"""\
[foo]
bar = fish
    """

    s2 = u"""\
\ufeff[foo]
bar = mammal
baz = Marc-Andr\202
    """

    def basic_tests(self, s, strable):
        f = StringIO(s)
        i = ini.INIConfig(f)
        self.assertEqual(unicode(i), s)
        self.assertEqual(type(i.foo.bar), unicode)
        if strable:
            self.assertEqual(str(i), str(s))
        else:
            self.assertRaises(UnicodeEncodeError, lambda: str(i))
        return i
    basic_tests.__test__ = False

    def test_ascii(self):
        i = self.basic_tests(self.s1, strable=True)
        self.assertEqual(i.foo.bar, 'fish')

    def test_unicode_without_bom(self):
        i = self.basic_tests(self.s2[1:], strable=False)
        self.assertEqual(i.foo.bar, 'mammal')
        self.assertEqual(i.foo.baz, u'Marc-Andr\202')

    def test_unicode_with_bom(self):
        i = self.basic_tests(self.s2, strable=False)
        self.assertEqual(i.foo.bar, 'mammal')
        self.assertEqual(i.foo.baz, u'Marc-Andr\202')

class suite(unittest.TestSuite):
    def __init__(self):
        unittest.TestSuite.__init__(self, [
                unittest.makeSuite(test_unicode, 'test'),
    ])
