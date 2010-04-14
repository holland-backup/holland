# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages

version = '0.9.9'

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
      packages=find_packages(exclude=["ez_setup", "examples"]),
      include_package_data=True,
      zip_safe=True,
      install_requires=[],
      tests_require=['nose', 'mocker', 'coverage'],
      test_suite='nose.collector',
      entry_points="""
      [holland.backup]
      mysql-lvm = holland.backup.lvm.plugin:LVMBackup
      
      [holland.restore]
      mysql-lvm = holland.restore.lvm:LVMRestore
      """,
      namespace_packages=['holland', 'holland.backup', 'holland.restore'],
      )
