from setuptools import find_packages, setup

version = "1.2.4"

setup(
    name="holland.backup.mysqldump",
    version=version,
    description="MySQLDump Backup/Restore Plugins",
    long_description="""\
      Plugin support to provide backup and restore functionality
      through mysqldump backups
      """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://hollandbackup.org",
    license="GNU GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    include_package_data=True,
    zip_safe=True,
    test_suite="tests",
    tests_require=["holland >= 0.9.6"],
    install_requires=[],
    extras_require={"mysql": "holland.lib.mysql", "common": "holland.lib.common"},
    entry_points="""
      [holland.backup]
      mysqldump = holland.backup.mysqldump:Provider [mysql, common]

      [holland.restore]
      mysqldump = holland.restore.mysqldump:MySQLRestore
      """,
    namespace_packages=["holland", "holland.backup"],
)
