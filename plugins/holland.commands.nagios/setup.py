from setuptools import setup, find_packages

version = '1.0.15'

setup(name='holland.commands.nagios',
      version=version,
      description="Nagios plugin for holland",
      long_description="""\
      Nagios command to check backup retention
      """,
      author='Jose Arthur Benetasso Villanova',
      author_email='jose.arthur@locaweb.com.br',
      url='',
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
      [holland.commands]
      nagios = holland.commands.nagios:Nagios
      """,
      namespace_packages=['holland', 'holland.commands'],
    )
