# Installing Holland
## RHEL/Centos from EPEL
### Setup EPEL
Instructions can be found here: https://fedoraproject.org/wiki/EPEL
### Install base packages and plugins
```
# yum install holland holland-common
# yum install holland-{plugin name}
```

## Ubuntu
### Install package from OBS
```
# . /etc/os-release
# echo "deb https://download.opensuse.org/repositories/home:/holland-backup/x${NAME}_${VERSION_ID}/ ./" >> /etc/apt/sources.list
# wget -qO -  https://download.opensuse.org/repositories/home:/holland-backup/x${NAME}_${VERSION_ID}/Release.key |apt-key add -
# apt-get update
# apt-get install holland {python3-mysqldb, python3-pymongo, ext...)
  ```

## SUSE
### Install package from OBS
```
# . /etc/os-release
# zypper ar -f https://download.opensuse.org/repositories/home:/holland-backup/$(echo $PRETTY_NAME|sed -e 's/ /_/g')/ holland
# zypper install holland holland-mysqldump
  ```

## Debian 9 and older
### Install package from OBS
```
# . /etc/os-release
# echo "deb http://download.opensuse.org/repositories/home:/holland-backup/Debian_${VERSION_ID}.0/ ./" >> /etc/apt/sources.list
# wget -qO -  https://download.opensuse.org/repositories/home:/holland-backup/Debian_${VERSION_ID}.0/Release.key |apt-key add -
# apt-get update
# apt-get install holland {python3-mysqldb, python3-pymongo, ext...)
```

## Debian 10
### Install package from OBS
```
# . /etc/os-release
# echo "deb https://download.opensuse.org/repositories/home:/holland-backup/Debian_${VERSION_ID}/ ./" >> /etc/apt/sources.list
# wget -qO -  https://download.opensuse.org/repositories/home:/holland-backup/Debian_${VERSION_ID}/Release.key |apt-key add -
# apt-get update
# apt-get install holland {python3-mysqldb, python3-pymongo, ext...)
```

## Docker
Third party Docker containers have been created and can be found here:
* https://hub.docker.com/r/sylabsio/cloud-services/
* https://github.com/sylabs/services-base-images/tree/docker/holland-backup-alpine

Please see their documentation for details on how to install and use these containers

## Manual
### Clone repo
```
# git clone https://github.com/holland-backup/holland.git ${TARGET}/holland
```

### Change directory and pull in submodules
```
# cd ${TARGET}/holland
# git submodule update --init --recursive
```

### Install base
** Requires Python Setuptool
```
# python setup.py install
```

### Create documentation
** Requires make and Sphinx > 1.7
```
# cd ${TARGET}/holland/docs && make man
# cp ${TARGET}/holland/build/man/holland.1 /usr/share/man/man1/
```

### Install common plugins
```
# cd ${TARGET}/holland/plugins/holland.lib.common/
# python setup.py install
```

### Most plugins require the holland.lib.mysql plugin
** The MySQldb connector requires gcc, mysql-devel, and python-devel
```
# cd ${TARGET}/holland/plugins/holland.lib.mysql/
# python setup.py install
```

### Install other plugins
```
# cd ../holland.backup.{plugin name}
# python setup.py install
```

### Setup configuration files
```
# mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
# cp ${TARGET}/holland/config/holland.conf /etc/holland/
# cp ${TARGET}/holland/config/providers/* /etc/holland/providers/
```
