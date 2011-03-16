from setuptools import setup, find_packages


version = '1.0a1'

setup(
    name='Delphini',
    version=version,
    description="A mysql cluster backup plugin for holland",
    long_description="""
    A mysql cluster backup plugin for holland
    """,
    keywords='',
    author='Rackspace',
    author_email='holland-core@launchpad.net',
    url='http://www.hollandbackup.org/',
    license='GPLv2',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests', 'tests.*']),
    include_package_data=True,
    zip_safe=False,
    entry_points="""
    [holland.backup]
    mysql-cluster = delphini.plugin:Delphini
    jones = delphini.plugin:Delphini
    """
)
