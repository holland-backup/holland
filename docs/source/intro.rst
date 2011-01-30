Introduction to Holland
=======================

Holland is an Open Source backup framework originally developed by Rackspace 
and written in Python. It's goal is to help facilitate backing up databases 
with greater configurability, consistency, and ease. Holland currently 
focuses on MySQL, however future development will include other database 
platforms and even non-database related applications. Because of it's 
plugin structure, Holland can be used to backup anything you want by 
whatever means you want.

Plugins are as normal Python packages and loaded via setuptools' entrypoints.

Dependencies
------------
The core Holland framework has the following requirements: 

* Python >= 2.3
* ``pkg_resources <http://packages.python.org/distribute/pkg_resources.html>``
* ``setuptools <http://packages.python.org/distribute>``

Plugins distributed with Holland will have additional requirements. For most
MySQL plugins you will additionally need:

* ``MySQLdb <http://mysql-python.sourceforge.net>``
* MySQL-4.1+ clients library and tools
