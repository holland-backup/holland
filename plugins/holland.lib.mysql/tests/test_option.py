import tempfile
import sys
from nose.tools import *
from holland.lib.mysql.option.legacy import OptionFile
from holland.lib.mysql.option.base import load_options, write_options

def test_load_options():
    fileobj = tempfile.NamedTemporaryFile()
    print >>fileobj, "[client]"
    print >>fileobj, "user = root"
    print >>fileobj, 'password = "foo"barbaz"'
    print >>fileobj, 'single-transaction=1'
    print >>fileobj
    print >>fileobj, '[mysqldump]'
    print >>fileobj, 'master-data = 2'
    print >>fileobj
    fileobj.flush()
    fileobj.seek(0)

    config = load_options(fileobj.name)
    assert_equals(config['client']['user'], 'root')
    assert_equals(config['client']['password'], 'foo"barbaz')

def test_write_options():
    fileobj = tempfile.NamedTemporaryFile()
    print >>fileobj, "[client]"
    print >>fileobj, "user = root"
    print >>fileobj, 'password = "foo"barbaz"'
    print >>fileobj, '[mysqldump]'
    print >>fileobj, 'master-data = 2'
    print >>fileobj
    fileobj.flush()
    fileobj.seek(0)

    config = load_options(fileobj.name)

    write_options(config, fileobj.name)

def test_load_options_with_errors():
    fileobj = tempfile.NamedTemporaryFile()
    print >>fileobj, "[client]"
    print >>fileobj, "user = root"
    print >>fileobj, 'password = "foo"barbaz"'
    print >>fileobj, 'single-transaction=1'
    print >>fileobj
    print >>fileobj, '[mysqldump]'
    print >>fileobj, 'master-data = 2'
    # ConfigObj won't support bare options like these
    # check that load_options skip them cleanly
    print >>fileobj, 'skip-dump-data'
    print >>fileobj, 'skip-lock-tables'
    print >>fileobj
    fileobj.flush()
    fileobj.seek(0)

    config = load_options(fileobj.name)

# configobj is quirky and will raise ParseError w/ one error
# and ConfigObjError w/ a errors attribute when there are
# multiple errors.  Let's test that we handle this
def test_load_options_with_one_error():
    fileobj = tempfile.NamedTemporaryFile()
    print >>fileobj, "[client]"
    print >>fileobj, "user = root"
    print >>fileobj, 'password = "foo"barbaz"'
    print >>fileobj, 'single-transaction=1'
    print >>fileobj
    print >>fileobj, '[mysqldump]'
    print >>fileobj, 'master-data = 2'
    # ConfigObj won't support bare options like these
    # check that load_options skip them cleanly
    print >>fileobj, 'skip-lock-tables'
    print >>fileobj
    fileobj.flush()
    fileobj.seek(0)

    config = load_options(fileobj.name)
