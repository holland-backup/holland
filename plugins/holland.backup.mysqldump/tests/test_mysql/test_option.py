# pylint: skip-file

import logging
from io import StringIO
from textwrap import dedent
from holland.backup.mysqldump.mysql.option import *
from holland.backup.mysqldump.mock.storage import replace_builtins, restore_builtins
from nose.tools import ok_, assert_equals, assert_raises

__test__ = False

def test_parse_section():
    assert_equals(parse_section('[client]', 1, None), 'client')
    assert_raises(SyntaxError, parse_section, 'client]', 1, None)

def test_parse_single_option():
    assert_equals(parse_single_option('password="foobarbaz"',1,None), ('password', 'foobarbaz'))
    assert_raises(SyntaxError, parse_single_option, "password = 'foo", 1, None)

def test_parse_bad_single_option():
    assert_raises(SyntaxError, parse_single_option, "'password' = foo", 1, None)

def test_parse_options():
    option_file = StringIO(dedent("""
        # Sample option file

        [client]
        user = "root"
        password = "Ziya8ln12"
        """).strip()
    )
    result = parse_options(option_file)
    ok_('client' in result)
    ok_('user' in result['client'])
    ok_('password' in result['client'])
    assert_equals(result['client']['password'], 'Ziya8ln12')
    assert_equals(result['client']['user'], 'root')

def test_parse_invalid_options():
    option_file = StringIO(dedent("""
        # Option with with no section

        user = "root"
        password = "Blah blah blah"
        """).strip()
    )
    assert_raises(SyntaxError, parse_options, option_file)

def test_unquote():
    assert_equals(unquote('"foo"'), 'foo')
    assert_equals(unquote('foo'), 'foo')

STD_DEFAULTS_FILE = StringIO("""
# A sample defaults file

[client]
user = "root"
password = "some other password"

[mysqldump]
single-transaction
all-databases
""")


def test_write_options():
    replace_builtins()
    try:
        write_options(SAMPLE_OPTIONS, '/mysql_defaults.conf')
        stream = open('/mysql_defaults.conf')
        assert_equals(parse_options(stream), SAMPLE_OPTIONS)
    finally:
        restore_builtins()
    ok_(not os.path.exists('/mysql_defaults.conf'),
            "Fake filesystem failure (FFF)")

def test_write_options_stream():
    try:
        stream_out = StringIO()
        write_options(SAMPLE_OPTIONS, stream_out)
        stream_in = StringIO(stream_out.getvalue())
        assert_equals(parse_options(stream_in), SAMPLE_OPTIONS)
    finally:
        pass

EMPTY_CONF = StringIO("""
[client]
""")

def test_write_options_empty_section():
    assert_equals(parse_options(EMPTY_CONF), {})
    output = StringIO()
    write_options({ 'client' : {} }, output)
    assert_equals(output.getvalue(), "")

def test_parse_options_multivalue():
    mysqldump_cnf = StringIO("""
    [mysqldump]
    ignore-table = mysql.user
    ignore-table = mysql.db
    ignore-table = mysql.proc
    ignore-table = mysql.time_zone
    """)
    assert_equals(parse_options(mysqldump_cnf), { 'mysqldump' : { 'ignore-table' : 'mysql.time_zone' } })

def test_write_options_multivalue():
    mysqldump_options = {
        'mysqldump' : {
            'ignore-table' : ['mysql.user', 'mysql.db', 'mysql.proc', 'mysql.timezone']
        }
    }
    expected = dedent("""
    [mysqldump]
    ignore-table = mysql.user
    ignore-table = mysql.db
    ignore-table = mysql.proc
    ignore-table = mysql.timezone
    """).lstrip()
    result = StringIO()
    write_options(mysqldump_options, result)
    assert_equals(result.getvalue(), expected)

def test_client_sections():
    mixed_cnf = StringIO("""
    [client]
    user = root
    password = "foo bar baz"
    default-character-set = utf8

    [mysqldump]
    single-transaction
    compact
    """)

    options_dict = parse_options(mixed_cnf)
    client_config = client_sections(options_dict)
    assert_equals(client_config, { 'client' : { 'user' : 'root', 'password' : 'foo bar baz' } })

def test_merge_option_dicts():
    global_my_cnf = StringIO("""
    [client]
    user = backup
    host = "192.168.100.250"
    port = 3306
    """)

    local_my_cnf = StringIO("""
    [client]
    password = "bar"
    """)

    global_config = parse_options(global_my_cnf)
    local_config = parse_options(local_my_cnf)
    assert_equals(merge_option_dicts(local_config, global_config),
                    { 'client' : {
                        'user' : 'backup',
                        'host' : '192.168.100.250',
                        'port' : '3306',
                        'password' : 'bar'
                        }
                    })

def test_merge_option_dicts_disjoint_sections():
    global_my_cnf = StringIO("""
    [holland]
    user = backup
    host = "192.168.100.250"
    port = 3306
    """)

    local_my_cnf = StringIO("""
    [client]
    password = "bar"
    """)

    global_config = parse_options(global_my_cnf)
    local_config = parse_options(local_my_cnf)
    assert_equals(merge_option_dicts(local_config, global_config),
                    { 'holland' : {
                        'user' : 'backup',
                        'host' : '192.168.100.250',
                        'port' : '3306',
                      },
                      'client' : {
                        'password' : 'bar',
                      }
                    })
