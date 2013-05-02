Introduction to Holland
=======================

Holland is an Open Source backup framework originally developed by Rackspace 
and written in Python. The original intent was to offer more reliability and
flexilibity when backing up MySQL databases, though the current version is
now able to backup MySQL and PostgreSQL databases. Because Holland is 
plugin-based framework, it can conceivably backup most anything you want
by whatever means you want.

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
the base channels.  Red-Hat Enterprise Linux 4, EPEL is required for
python-setuptools. 

Note that other plugins may have additional dependency requirements.

Installation
------------
Holland has ready-made packages available for Red-Hat, CentOS, and Ubuntu
which are available via the OpenSUSE build system 
`here <http://download.opensuse.org/repositories/home:/holland-backup/>`_.
Other distributions may download the generic tarball
`here <http://hollandbackup.org/releases/stable/1.0/>`_ or pull directly
from the GitHub tree `here <https://github.com/holland-backup/holland>`_.

