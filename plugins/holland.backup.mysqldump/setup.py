from setuptools import setup, find_packages

version = '1.1.0'

setup(name='holland.backup.mysqldump',
      version=version,
      description="MySQLDump Backup/Restore Plugins",
      long_description="""\
      Plugin support to provide backup and restore functionality
      through mysqldump backups
      """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://hollandbackup.org',
      license='GNU GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'tests.*']),
      include_package_data=True,
      zip_safe=True,
      test_suite='tests',
      install_requires=[
        # 'nose', # Not required, but needed if you want to run nose tests...
      ],
      entry_points="""
      [holland.backup]
      mysqldump = holland.backup.mysqldump:provider

      [holland.hooks]
      mysql-select = holland.lib.mysqldump:MySQLSelectHook
      """,
      namespace_packages=['holland', 'holland.lib', 'holland.backup'],
    )
