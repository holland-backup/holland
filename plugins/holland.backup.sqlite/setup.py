from setuptools import setup, find_packages

version = "1.1.13"

setup(
    name="holland.backup.sqlite",
    version=version,
    description="SQLite Backup Plugin for Holland",
    long_description="""\
      Dump SQLite databases into pure ASCII SQL text for archiving.
      """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="sqlite backup",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    include_package_data=True,
    zip_safe=True,
    test_suite="tests",
    install_requires=[
        # -*- Extra requirements: -*-
    ],
    entry_points="""
      [holland.backup]
      sqlite = holland.backup.sqlite:SQLitePlugin
      """,
    namespace_packages=["holland", "holland.backup"],
)
