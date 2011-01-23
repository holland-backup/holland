[mysql-lvm]
# default: mysql lv + _snapshot
snapshot-name = string(default=None)

# default: minimum of 20% of mysql lv or mysql vg free size
snapshot-size = string(default=None)

# default: temporary directory
snapshot-mountpoint = string(default=None)

# default: no
innodb-recovery = boolean(default=no)

# default: flush tables with read lock by default
lock-tables = boolean(default=yes)

# default: do an extra (non-locking) flush tables before
#          run flush tables with read lock
extra-flush-tables = boolean(default=yes)

[mysqld]
mysqld-exe              = force_list(default=list('mysqld',
                                                  '/usr/libexec/mysqld'))
user                    = string(default='mysql')
innodb-buffer-pool-size = string(default=128M)
tmpdir                  = string(default=None)

[tar]
exclude = force_list(default='mysql.sock')

[compression]
method = option('none', 'gzip', 'pigz', 'bzip2', 'lzop', default='gzip')
level = integer(min=0, max=9, default=1)

[mysql:client]
# default: ~/.my.cnf
defaults-file = string(default='~/.my.cnf')
defaults-extra-file = force_list(default=list('~/.my.cnf'))

# default: current user
user = string(default=None)

# default: none
password = string(default=None)

# default: localhost
host = string(default=None)

# default: 3306
port = integer(default=None)
# default: none
socket = string(default=None)
