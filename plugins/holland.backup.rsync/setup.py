from setuptools import setup, find_packages

version = '1.0.10'

setup(name='holland.backup.rsync',
      version=version,
      description="rsync Plugin for Holland",
      long_description="""\
      rsync plugin for the Holland backup framework
      """,
      author='Tim Soderstrom',
      author_email='holland-devel@googlegroups.com',
      url='http://www.hollandbackup.org/',
      license='GPLv2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests',
                                      'tests.*']),
      include_package_data=True,
      zip_safe=False,
      test_suite='tests',
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      [holland.backup]
      rsync = holland.backup.rsync:RsyncPlugin
      """,
      namespace_packages=['holland', 'holland.backup'],
    )
