from setuptools import setup, find_packages

version = '1.1.1'

setup(name='holland.lib.mysql',
      version=version,
      description="Holland MySQL Support",
      install_requires=[
      ],
      long_description="""
        Provides convenience methods for MySQL
      """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://www.hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'tests.*']),
      include_package_data=True,
      zip_safe=True,
      tests_require=['mocker==0.10.1', 'coverage==2.85'],
      test_suite='tests',
      entry_points="""
      # -*- Entry points: -*-
      [holland.lib]
      mysql = holland.lib.mysql:MySQLClient
      mycmdparser = holland.lib.mysql:MyCmdParser
      """,
      namespace_packages=['holland', 'holland.lib']
      )
