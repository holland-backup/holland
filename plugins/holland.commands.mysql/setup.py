from setuptools import setup, find_packages

version = '0.9.9'

setup(name='holland.commands.mysql',
      version=version,
      description="Extra commands for managing MySQL backups and restores",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://www.hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      test_suite='tests',
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [holland.commands]
      mysql-restore = holland.commands.mysql_restore:MySQLRestore
      mysql-list    = holland.commands.mysql_index_list:MySQLIndexList
      mysql-extract = holland.commands.mysql_extract_table:MySQLExtractTable
      """,
      namespace_packages=['holland','holland.commands']
      )
