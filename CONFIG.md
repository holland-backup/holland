# Holland Configurations
## Overview
This document provides a brief look at the configuration files commonly used while configuration Holland backups. To start, there are several different providers in holland and each one brings different strengths and weaknesses to the table. Understanding the different providers is fundamental to working with holland.   

Thanks to [THE-Alan-Hicks](https://github.com/THE-Alan-Hicks) for writting this document. 

# Holland Configuration Files
Let's begin by taking a quick look at what files and directories we can expect to see in /etc/holland.
```
# find /etc/holland/ 
/etc/holland/ 
/etc/holland/holland.conf 
/etc/holland/backupsets 
/etc/holland/backupsets/host2.conf 
/etc/holland/backupsets/localhost.conf 
/etc/holland/backupsets/host1.conf 
/etc/holland/providers 
/etc/holland/providers/mysql-lvm.conf 
/etc/holland/providers/mysqldump-lvm.conf 
/etc/holland/providers/mysqldump.conf   
```
Right away you should notice that the layout here is unusual. Normally you might expect to find a single configuration file, such as holland.conf, and indeed we have such a file. However, holland doesn't work that way. Instead, it utilizes several configuration files (some of which could be unused). Let's take a closer look at each in turn.
/etc/holland/holland.conf
```
# egrep -v '^\s*#|^\s*$' /etc/holland/holland.conf 
[holland]
plugin_dirs                  = /usr/share/holland/plugins
backup_directory             = /var/spool/holland
backupsets                   = localhost 
umask                        = 0007
path                         = /usr/local/bin:/usr/local/sbin:/bin:/sbin:/usr/bin:/usr/sbin
[logging]
filename                     = /var/log/holland/holland.log
level                        = info  
```
This file is split up in a manner similar to /etc/my.cnf, but doesn't have nearly as many options. Most of the configuration is offloaded to other files. Since the [logging] section should be fairly self-explanatory, let's take a look at the [holland] section first. Here we see where to look for installed plugins (plugin_dirs), the directory where backups will be placed (backup_directory), the backupsets which will be used (more than one can be specified), and the umask and path variables.
/etc/holland/providers/*.conf
The /etc/holland/providers directory contains configuration files for each different type of holland backup supported (mysqldump, lvm, xtrabackup, etc.). These files contain configuration information such as how to login to the database server along with default configuration options for each type.
```
# find /etc/holland/providers/
/etc/holland/providers/
/etc/holland/providers/mysql-lvm.conf
/etc/holland/providers/mysqldump-lvm.conf
/etc/holland/providers/mysqldump.conf
```
## mysqldump.conf  
```
# egrep -v '^\s*#|^\s*$' /etc/holland/providers/mysqldump.conf 
[mysqldump]
lock-method                  = auto-detect
dump-routines                = no
dump-events                  = no
stop-slave                   = no
bin-log-position             = no
flush-logs                   = no
file-per-database            = no
additional-options           = ""
[compression]
method                       = gzip
inline                       = yes
level                        = 1
[mysql:client]
defaults-extra-file          = /root/.my.cnf,~/.my.cnf,
```
## mysql-lvm.conf  
```
# egrep -v '^\s*#|^\s*$' /etc/holland/providers/mysql-lvm.conf 
[mysql-lvm]
snapshot-size                = ""   # default 20%
snapshot-name                = "" # no default
snapshot-mountpoint          = "" # no default
innodb-recovery              = False
lock-tables                  = True
extra-flush-tables           = True
[compression]
method                       = gzip
level                        = 1
[mysql:client]
defaults-file                = /root/.my.cnf
```
## mysqldump-lvm.conf  
```
# egrep -v '^\s*#|^\s*$' /etc/holland/providers/mysqldump-lvm.conf 
[mysql-lvm]
lock-tables                  = yes
extra-flush-tables           = yes
[mysqld]
mysqld-exe                   = mysqld, /usr/libexec/mysqld
user                         = mysql
innodb-buffer-pool-size      = 128M
key-buffer-size              = 16M
[mysqldump]
extra-defaults               = no
mysql-binpath                = ,
lock-method                  = auto-detect
databases                    = *,
exclude-databases            = ,
tables                       = *,
exclude-tables               = ,
engines                      = *,
exclude-engines              = ,
flush-logs                   = no
flush-privileges             = yes
dump-routines                = no
dump-events                  = no
stop-slave                   = no
max-allowed-packet           = 128M
bin-log-position             = no
file-per-database            = yes
additional-options           = ,
estimate-method              = plugin
[compression]
method                       = gzip
inline                       = yes
level                        = 1
[mysql:client]
defaults-extra-file          = ~/.my.cnf,  
```
We won't be delving into every available option here. Just familiarize yourself with the options that are most common between the different types for now. I've removed all comments for brevity. If you need these, see the examples in /usr/share/doc/holland-${VERSION}/examples/. Some of this will become more clear when we look at some examples later.
/etc/holland/backupsets/*.conf
The /etc/holland/backupsets directory tells us what backupsets are available for use.  
```
# find /etc/holland/backupsets/
/etc/holland/backupsets/host1.conf
/etc/holland/backupsets/host2.conf
/etc/holland/backupsets/localhost.conf
```
Here we have three different backupsets that can be configured. Again, more than one can be specified, but canonically you'll only see a single one listed - default.conf. Everything before the .conf in the filename is a legitimate value for the backupsets variable in holland.conf. These files are very similar to those found in providers/ with one key difference. The providers/ directory contains configuration files for each backup type, while backupsets/ contains configuration files for each backup job. This distinction is important. Holland can be configured to run multiple backupsets while only performing one type of backup (e.g. mysqldump).
Recall the backupsets variable from /etc/holland/holland.conf. This variable tells us which configuration files in /etc/holland/backupsets/ should be read and followed. In our example we had the following configuration.  
```
# grep '^\s*backupsets' /etc/holland/holland.conf
backupsets                   = localhost
```
This tells us that /etc/holland/backupsets/localhost.conf (and no other files in this directory) will be used to create a backup job. So let's take a look at these files.
## localhost.conf  
```
[holland:backup]
plugin                       = mysqldump
backups-to-keep              = 1
auto-purge-failures          = yes
purge-policy                 = after-backup
estimated-size-factor        = 1.0
[mysqldump]
lock-method                  = auto-detect
databases                    = "*"
#exclude-databases           = 
tables                       = "*"
#exclude-tables              = ""
dump-routines                = no
dump-events                  = no
stop-slave                   = no
bin-log-position             = no
flush-logs                   = no
file-per-database            = no
additional-options           = ""
## Compression Settings
[compression]
method                       = gzip
inline                       = yes
level                        = 1
#[mysql:client]
#user                        = hollandbackup
#password                    = "hollandpw"
#socket                      = /tmp/mysqld.sock
#host                        = localhost
#port                        = 3306
host1.conf  
[holland:backup]
plugin                       = mysql-lvm
backups-to-keep              = 1
auto-purge-failures          = yes
purge-policy                 = after-backup
estimated-size-factor        = 1.0
[mysql-lvm]
#snapshot-size               = ""   # default 20%
#snapshot-name               = "" # no default
#snapshot-mountpoint         = "" # no default
#innodb-recovery             = False
#lock-tables                 = True
#extra-flush-tables          = True
## Compression Settings
[compression]
method                       = gzip
level                        = 1
#[mysql:client]
#user                        = hollandbackup
#password                    = "hollandpw"
#socket                      = /tmp/mysqld.sock
#host                        = localhost
#port                        = 3306
host2.conf  
[holland:backup]
plugin                       = mysqldump-lvm
backups-to-keep              = 1
auto-purge-failures          = yes
purge-policy                 = after-backup
estimated-size-factor        = 1.0
## LVM Backup Specific Settings
[mysql-lvm]
#snapshot-size               = ""   # default 20%
#snapshot-name               = "" # no default
#snapshot-mountpoint         = "" # no default
lock-tables                  = True
extra-flush-tables           = True
[mysqld]
user                         = mysql
innodb-buffer-pool-size      = 128M
key-buffer-size              = 128M
#mysqld-exe                  = /usr/libexec/mysqld
[mysqldump]
file-per-database            = yes
lock-method                  = lock-tables
#databases                   = "*"
#tables                      = "*"
#stop-slave                  = no
#bin-log-position            = no
[compression]
method                       = gzip
inline                       = True
level                        = 1
[mysql:client]
#defaults-file               = /root/.my.cnf
#user                        = "" # no default
#password                    = "" # no default  
```
As we previously mentioned, these files closely mirror those found in /etc/holland/providers/ with one key difference - the [holland:backup] section. This section tells us what plugin to use (mysqldump, mysql-lvm, etc.), how many backups-to-keep, the purge-policy and similar options. The plugin value tells holland which type of backup to perform along with which configuration file in /etc/holland/providers/ needs to be read. The backupsets configuration files overwrite any options specific in providers/. This means that some set of sane defaults can be set in (for example) /etc/holland/providers/mysqldump.conf and then two different backupsets can be configured using those defaults.
# Backup Types
Commanly used backup types
## mysqldump
This is the simplest of all backup operations. Holland simply performs a standard mysqldump. Commandline options are built based on the configuration options specified in the provider and backupset configuration files.
## mysql-lvm
This is the fastest of all backup solutions. This works by taking a a lock of the database followed by a filesystem snapshot, releasing the lock, then backing up that snapshot into a tarball. There are a few things to keep in mind when working with mysql-lvm.
•	The volume group must have enough free extents to create a snapshot of the size specified
•	The snapshot size must be large enough to contain all the changes being made to the active filesystem by the running mysql service
•	The holland backup_directory location must be on a different filesystem than the running database. If they exist on the same filesystem, then the tar operation will consume extents in the snapshot and performance will be abysmal.
## mysqldump-lvm
This is a combination of the previous methods. It contains all the constraints of mysql-lvm, but produces sql files rather than a tarball. Here's what happens behind the scenes. 

1.	holland performs a read-lock on the database
2.	A filesystem snapshot is taken
3.	holland releases the read-lock
4.	The snapshot is mounted
5.	holland spins up an additional mysqld service reading its data from that snapshot
6.	holland performs a mysqldump on this secondary instance
7.	The secondary instance is terminated and the snapshot unmounted
8.	The snapshot is deleted.

## mariabackup && xtrabackup
These plugins using the mariabackup and xtrabackup command to perform dumps

## mongodump
Holland performs a mongodump on the database

# References

•	[Holland Configuration Files](http://docs.hollandbackup.org/config.html)
