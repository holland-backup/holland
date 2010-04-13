from setuptools import setup, find_packages
import sys, os

version = '0.4'

setup(name='holland.backup.xtrabackup',
      version=version,
      description="Percona XtraBackup Plugin",
      long_description="""\
      Percona XtraBackup is an OpenSource online (non-blockable) backup 
      solution for InnoDB and XtraDB engines.
      """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='holland backup percona xtrabackup ibbackup',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
