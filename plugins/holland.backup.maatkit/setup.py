from setuptools import setup, find_packages

version = '1.0.0'

setup(name='holland.backup.maatkit',
      version=version,
      description="Maatkit Parallel Backup Plugin",
      long_description="""\
      Provides support for using Maatkit's mk-parallel-dump
      script.    
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
      install_requires=[
      ],
      entry_points="""
      [holland.backup]
      maatkit = holland.backup.maatkit:provider
      """,
      namespace_packages=['holland','holland.backup']
      )
