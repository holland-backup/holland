from setuptools import setup, find_packages

version = '1.0.12'

setup(name='holland.backup.mysqlhotcopy',
      version=version,
      description="MySQL (MyISAM) Hotcopy Plugin",
      long_description="""\
      Backup raw MyISAM files
      """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://hollandbackup.org/',      
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=True,
      tests_require='holland.lib.mysql',
      test_suite='tests',
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [holland.backup]
      mysqlhotcopy = holland.backup.mysqlhotcopy:provider
      """,
      namespace_packages=['holland', 'holland.backup'],
      )
