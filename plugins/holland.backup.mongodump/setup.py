from setuptools import setup, find_packages
import sys, os

version = '1.0.15'

setup(name='holland.backup.mongodump',
      version=version,
      description="Holland mongodump backup plugin",
      long_description="""\
      Postgres mongodump backup""",
      author='Locaweb',
      author_email='jose.arthur@locaweb.com.br',
      url='https://github.com/holland-backup/holland/',
      license='GNU GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'tests.*']),
      namespace_packages=['holland', 'holland.backup'],
      zip_safe=True,
      # holland looks for plugins in holland.backup
      entry_points="""
      [holland.backup]
      mongodump = holland.backup.mongodump:MongoDump
      """
)
