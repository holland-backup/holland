from setuptools import setup, find_packages


version = '1.0'

setup(
    name='holland.backup.delphini',
    version=version,
    description="A mysql cluster backup plugin for holland",
    long_description="""
    A mysql cluster backup plugin for holland
    """,
    keywords='',
    author='Holland Core Development Team',
    author_email='holland-core@launchpad.net',
    url='http://www.hollandbackup.org/',
    license='BSD',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'tests.*']),
    include_package_data=True,
    zip_safe=False,
    entry_points="""
    [holland.backup]
    mysql-cluster   = delphini:DelphiniPlugin
    delphini        = delphini:DelphiniPlugin
    """,
    namespace_packages=['holland', 'holland.backup'],
)
