from setuptools import setup, find_packages

version = '1.0.3'

setup(name='holland.backup.xtrabackup',
      version=version,
      description="Xtrabackup Plugin for Holland",
      long_description="""\
      Xtrabackup plugin for the Holland backup framework
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
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [holland.backup]
      xtrabackup = holland.backup.xtrabackup:XtrabackupPlugin
      """,
      namespace_packages=['holland', 'holland.backup'],
    )
