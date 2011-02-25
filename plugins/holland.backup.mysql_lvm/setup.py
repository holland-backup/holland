# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages

version = '1.0.6'

setup(name="holland.backup.mysql_lvm",
      version=version,
      description="MySQL/LVM Snapshot Plugin",
      long_description="""\
      This script provides support for performing safe LVM snapshot backups
      for MySQL databases.
      """,
      classifiers=[],
      keywords="",
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://www.hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
      include_package_data=True,
      zip_safe=True,
      install_requires=[],
      tests_require=['nose', 'mocker', 'coverage'],
      test_suite='nose.collector',
      entry_points="""
      [holland.backup]
      mysql-lvm = holland.backup.mysql_lvm:MysqlLVMBackup
      mysqldump-lvm = holland.backup.mysql_lvm.plugin.mysqldump:MysqlDumpLVMBackup
      """,
      namespace_packages=['holland', 'holland.backup'],
      )
