Introduction to Holland
=======================

Holland is an Open Source backup framework originally developed by Rackspace 
and written in Python. It's goal is to help facilitate backing up databases 
with greater configurability, consistency, and ease. Holland currently 
focuses on MySQL, however future development will include other database 
platforms and even non-database related applications. Because of it's 
plugin structure, Holland can be used to backup anything you want by 
whatever means you want.

Plugins are provided as Python "eggs" - zip files with Python modules and
extra metadata information.

Dependencies
------------
The core Holland framework has the following dependencies (available on any
remotely modern Linux distribution):

* Python >= 2.3
* `pkg_resources <http://peak.telecommunity.com/DevCenter/PkgResources>`_
* `python-setuptools <http://peak.telecommunity.com/DevCenter/setuptools>`_
* `MySQLdb <http://mysql-python.sourceforge.net/>`_

Additionally, the Maatkit plugin requires:

* `Maatkit <http://maatkit.org>`_
* `Perl-TermReadKey <http://search.cpan.org/~kjalb/TermReadKey/ReadKey.pm>`_

For Red-Hat Enterprise Linux 5, all dependencies, except for Maatkti, are
available directly from the base channels. Red-Hat Enterprise Linux 4, 
EPEL is required for python-setuptools. 

Note that other providers may have additional dependency requirements.

