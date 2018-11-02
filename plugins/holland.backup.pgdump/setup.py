from setuptools import setup, find_packages
import sys, os

version = '1.1.9'

setup(name='holland.backup.pgdump',
      version=version,
      description="Holland pg_dump backup plugin",
      long_description="""\
      Postgres pg_dump backup""",
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='https://gforge.rackspace.com/gf/project/holland',
      license='GNU GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'tests.*']),
      namespace_packages=['holland', 'holland.backup'],
      zip_safe=True,
      install_requires=['psycopg2' ],
      # holland looks for plugins in holland.backup
      entry_points="""
      [holland.backup]
      pgdump = holland.backup.pgdump:PgDump
      """
)
