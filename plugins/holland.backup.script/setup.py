from setuptools import setup, find_packages
import sys, os

version = '1.0.7a1'

setup(name='holland.backup.script',
      version=version,
      description="Perform backups with simple shell commands",
      long_description="""
      """,
      author='Andrew Garner',
      author_email='muzazzi@gmail.com',
      url='http://hollandbackup.org',
      license='GPL2',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      entry_points="""
      [holland.backup]
      script = holland.backup.script:ScriptPlugin
      """,
      namespace_packages=['holland', 'holland.backup']
)
