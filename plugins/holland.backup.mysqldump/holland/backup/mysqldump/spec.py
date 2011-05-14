"""holland.backup.mysqldump configspec"""

CONFIGSPEC = """
[mysqldump]
extra-defaults     = boolean(default=yes)
explicit-tables    = boolean(default=yes)
mysql-binpath      = force_list(default=list())

lock-method                    = option('flush-lock', 'lock-tables',
                                        'single-transaction',
                                        'auto-detect',
                                        'none',
                                        default='auto-detect')
transactional-engines-override = list(default=list())
transactional-databases-override = list(default=list())
transactional-tables-override = list(default=list())
lockless-only      = boolean(default=no)

databases          = force_list(default=list('*'))
exclude-databases  = force_list(default=list())

tables             = force_list(default=list("*"))
exclude-tables     = force_list(default=list())

engines            = force_list(default=list("*"))
exclude-engines    = force_list(default=list())

flush-logs         = boolean(default=no)
flush-privileges   = boolean(default=yes)
dump-routines      = boolean(default=no)
dump-events        = boolean(default=no)
stop-slave         = boolean(default=no)
max-allowed-packet = string(default="128M")
bin-log-position   = boolean(default=no)

file-per-database  = boolean(default=yes)
parallelism        = integer(min=1, default=1)

additional-options = force_list(default=list())

estimate-method    = string(default='plugin')

[compression]
method = option('none', 'gzip', 'pigz', 'bzip2', 'lzma', 'lzop', default='gzip')
inline = boolean(default=yes)
level  = integer(min=0, max=9, default=1)

[mysql:client]
defaults-extra-file = force_list(default=list('~/.my.cnf'))
user                = string(default=None)
password            = string(default=None)
socket              = string(default=None)
host                = string(default=None)
port                = integer(min=0, default=None)
"""
