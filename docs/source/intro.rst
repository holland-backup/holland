Introduction to Holland
=======================

Holland is an Open Source backup framework originally developed by Rackspace 
and written in Python. It's goal is to help facilitate backing up databases 
with greater configurability, consistency, and ease. Holland currently 
focuses on MySQL, however future development will include other database 
platforms and even non-database related applications. Because of it's 
plugin structure, Holland can be used to backup anything you want by 
whatever means you want.

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
