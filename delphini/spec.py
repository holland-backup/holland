"""Config specification for mysql cluster backups"""

CONFIGSPEC = """
[mysql-cluster]
connect-string      = string(default='localhost')
default-ssh-user    = string(default='root')
default-ssh-keyfile = string(default=None)

[compression]
method              = option(gzip, pigz, bzip2, lzop, lzma, default=gzip)
level               = integer(min=0, max=9)
inline              = boolean(default=yes)
""".splitlines()
