from setuptools import setup, find_packages

version = '1.1.12'

setup(name='holland.backup.example',
      version=version,
      description=" Example Backup Plugin",
      long_description="""\
      An example backup plugin
      """,
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Rackspace',
      author_email='holland-devel@googlegroups.com',
      url='http://www.hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'tests.*']),
      include_package_data=True,
      zip_safe=True,
      test_suite='tests',
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [holland.backup]
      example = holland.backup.example:ExamplePlugin
      """,
      namespace_packages=['holland', 'holland.backup'],
    )
