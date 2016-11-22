Introduction to Holland
=======================

Holland is an Open Source backup framework originally developed by Rackspace
and written in Python. The original intent was to offer more reliability and
flexilibity when backing up MySQL databases, though the current version is
now able to backup MySQL and PostgreSQL databases. Because Holland is
plugin-based framework, it can conceivably backup most anything you want
by whatever means you want.

General Concepts
----------------
Holland is built around the concept of providers and backup-sets.

A provider implements a backup solution. This can range from backing up MySQL
databases using mysqldump, LVM, or Xtrabackup; to backing up a local or remote
directory using rsync.

A backup-set defines a backup and includes global parameters, such as which
provider will be used and how many backups to keep; as well as
provider-specific configuration options, such as databases to exclude, user
credentials, servers, etc. While some providers share similar options with
each other, for the most part each provider has its own set of configuration
options.

For more information, see :doc:`overview`

Dependencies
------------
The core Holland framework has the following dependencies (available on any
remotely modern Linux distribution):

* Python >= 2.3
* `pkg_resources <http://packages.python.org/distribute/pkg_resources.html>`_
* `python-setuptools <http://packages.python.org/distribute/>`_

MySQL based plugins additional require the MySQLdb python connector:

* `MySQLdb <http://mysql-python.sourceforge.net/>`_

For Red-Hat Enterprise Linux 5, all dependencies are available directly from
the base channels. For Red-Hat Enterprise Linux 4, EPEL is required for
python-setuptools.

Note that other plugins may have additional dependency requirements.

Installation
------------
Holland has ready-made packages available for Red-Hat, CentOS, and Ubuntu
which are available via the `OpenSUSE build system`_.
Other distributions may download the `generic tarball`_ or pull directly
from `github`_.

.. _OpenSUSE build system: http://download.opensuse.org/repositories/home:/holland-backup/
.. _generic tarball: http://hollandbackup.org/releases/stable/1.0/
.. _github: https://github.com/holland-backup/holland
