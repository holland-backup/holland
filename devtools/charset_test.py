import load_it
from holland.lib.mysql.client import MySQLClient

client = MySQLClient(read_default_group='client')
print client.encode_as_filename('foo/bar')
print client.encode_as_filename('foo.bar')
