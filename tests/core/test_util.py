from holland.core.util import path, fmt, pycompat
from nose.tools import *

# fmt tests
def test_format_interval():
    one_minute = 60
    assert_equals(fmt.format_interval(one_minute), '1 minute')
    two_minutes = 120
    assert_equals(fmt.format_interval(two_minutes), '2 minutes')
    two_weeks_5d_4h_39m_16s = 1658356

    assert_equals(fmt.format_interval(two_weeks_5d_4h_39m_16s),
                  '2 weeks, 5 days, 4 hours, 39 minutes, 16.00 seconds')


def test_format_datetime():
    from time import strftime, localtime

    assert_equals(fmt.format_datetime(0),
                  strftime('%a %b %d %Y %I:%M:%S%p', localtime(0)))

def test_format_bytes():
    f = fmt.format_bytes

    assert_equals(f(0), '0.00B')
    assert_equals(f(1), '1.00B')
    assert_equals(f(1024), '1.00KB')
    assert_equals(f(1024**2), '1.00MB')
    assert_equals(f(4831838208.0), '4.50GB')

    # negative bytes
    assert_equals(f(-1), '-1.00B')
    assert_equals(f(-1024), '-1.00KB')
    assert_equals(f(-(1024**2)), '-1.00MB')
    assert_equals(f(-4831838208.0), '-4.50GB')

    # change precision
    assert_equals(f(-4831838208.0, precision=4), '-4.5000GB')

    # really large values
    assert_raises(ArithmeticError, f, 1024**10)

# path tests

def test_relpath():
    assert_equals(path.relpath("/mnt/mysql-lvm", "/mnt/mysql-lvm"), "")
    assert_equals(path.relpath("/mnt/mysql-lvm", "/mnt/mysql-lvm/data"),
                  "data")

#XXX: linux specific
def test_getmount():
    test_path = "/proc/self/cmdline"
    assert_equals(path.getmount(test_path), "/proc")

#XXX: df output isn't 100% portable
#XXX: race condition between running df and disk_free()
def test_diskfree():
    import commands
    real_cmd = "df -B1 / | tail -n +2 | awk '{ print $4; }'"
    actual_bytes = int(commands.getoutput(real_cmd).strip())
    assert_equals(path.disk_free("/"), actual_bytes)

def test_directory_size():
    # must test that this equals du -sb
    # test symlinks and weird crap too
    import commands
    cmd = "du -sb . | awk '{ print $1; }'"
    expected_bytes = int(commands.getoutput(cmd).strip())
    assert_equals(path.directory_size('.'), expected_bytes)
    # test handling OSError as well - perhaps have an unreadable directory
    # also, in practice this function may be used against an active directory
    # that may have entries randomly deleted as we're stat'ing them
