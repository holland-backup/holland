.. _config:

Configuring Holland
===================

By default, Holland's configuration files reside in /etc/holland. The main
configuration file is holland.conf, however there are a number of other
configuration files for configuring default settings for providers and for
configuring backup sets.

Each configuration file has one ore more sections, defined by square
brackets Underneath each section, one or more configuration option
can be specified. These options are in a standard "option = value" format.
Comments are prefixed by the # sign.

Note that many settings have default values and, as a result, can either
be commented out or omitted entirely.

.. include:: config-global.rst

.. include:: config-backupsets.rst

Provider Plugin Configs
-----------------------

* :ref:`mysqldump <config-mysqldump>`: Backup MySQL using the mysqldump tool
* :ref:`mysql-lvm <config-mysql-lvm>`: Backup MySQL using LVM snapshots
* :ref:`mysqldump-lvm <config-mysqldump-lvm>`: Backup MySQL using mysqldump on top of an LVM snapshot
* :ref:`Xtrabackup <config-xtrabackup>`: Backup MySQL using Percona's Xtraabckup tool
* :ref:`pgdump <config-pgdump>`: Backup PostgreSQL using the pgdump tool

