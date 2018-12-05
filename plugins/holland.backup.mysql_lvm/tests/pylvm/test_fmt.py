# pylint: skip-file

import nose.tools
from holland.backup.lvm.pylvm.fmt import *

def test_prohibited_lvm_name():
    # 'snapshot' is prohibited
    nose.tools.assert_raises(SyntaxError, validate_name, 'snapshot')
    # _mlog or _image anywhere in a name is probihited
    nose.tools.assert_raises(SyntaxError, validate_name, 'foo_mlog')
    nose.tools.assert_raises(SyntaxError, validate_name, 'foo_mimage_bar')
    # names may not start with a '-'
    nose.tools.assert_raises(SyntaxError, validate_name, '-foo_bar_baz')

def test_valid_names():
    validate_name('mysql_snapshot')
    validate_name('mysql-snapshot')
    validate_name('09mysql19-snapshot-test')
