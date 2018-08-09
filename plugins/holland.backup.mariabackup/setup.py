from setuptools import setup, find_packages

version = '1.1.1'

setup(name='holland.backup.mariabackup',
      version=version,
      description="Holland plugin for MariaDB mariabackup",
      long_description="""\
      Holland plugin for MariaDB mariabackup
      """,
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
          # -*- Emaria requirements: -*-
      ],
      entry_points="""
      [holland.backup]
      mariabackup = holland.backup.mariabackup:MariabackupPlugin
      """,
      namespace_packages=['holland', 'holland.backup'],
    )
