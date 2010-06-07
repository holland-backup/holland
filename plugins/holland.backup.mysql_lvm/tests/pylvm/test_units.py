import holland.backup.lvm.pylvm.fmt
from nose.tools import *

def test_parse_size():
    ok_(holland.backup.lvm.pylvm.fmt.parse_size('42G') == (42 * 1024 ** 3))
    ok_(holland.backup.lvm.pylvm.fmt.parse_size('1024') == holland.backup.lvm.pylvm.fmt.parse_size('1024M'))
    ok_(holland.backup.lvm.pylvm.fmt.parse_size('42G') == holland.backup.lvm.pylvm.fmt.parse_size('43008M'))
    assert_raises(SyntaxError, holland.backup.lvm.pylvm.fmt.parse_size, '42Q')

def test_format_size():
    ok_(holland.backup.lvm.pylvm.fmt.format_size(holland.backup.lvm.pylvm.fmt.parse_size('42G'), 0) == '42G')
    ok_(holland.backup.lvm.pylvm.fmt.format_size(1024, 0) == '1K')
    ok_(holland.backup.lvm.pylvm.fmt.format_size(1024 ** 7, 0) == '1024E')
    assert_raises(ValueError, holland.backup.lvm.pylvm.fmt.format_size, 512)

def test_validate_size():
    ok_(holland.backup.lvm.pylvm.fmt.validate_size('12G') == '12.0000G')

    # Test that a string with an invalid unit generates a syntax error
    assert_raises(SyntaxError, holland.backup.lvm.pylvm.fmt.validate_size, '12Q')
    # Test that a valid unit that is otherwise unusable fails (e.g. < 1K)
    assert_raises(ValueError, holland.backup.lvm.pylvm.fmt.validate_size, '0.5K')
