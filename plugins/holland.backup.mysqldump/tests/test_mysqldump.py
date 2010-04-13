from holland.backup.mysqldump.mysql.dump import *
from nose.tools import assert_equals, assert_raises

__test__ = False

def test_collapse_extra_options():
    redundant_options = [
        '--master-data=2',
        '--master-data=2',
        '--master-data=2',
        '--single-transaction',
        '--single-transaction',
    ]

    collapse_extra_options(redundant_options)
    assert_equals(redundant_options, ['--master-data=2', '--single-transaction'])

def test_validate_invalid_option():
    assert_raises(Exception, validate_one_option, '--result-file=/etc/passwd')
