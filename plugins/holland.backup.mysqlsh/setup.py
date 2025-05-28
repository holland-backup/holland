from setuptools import find_packages, setup

version = "1.2.12"

setup(
    name="holland.backup.mysqlsh",
    version=version,
    description="Holland mysqlsh backup plugin",
    long_description="""\
      MySQL mysqlsh backup""",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GNU GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    namespace_packages=["holland", "holland.backup"],
    zip_safe=True,
    install_requires=[],
    entry_points={
        "holland.backup": [
            "dump-instance = holland.backup.mysqlsh:MySqlShDumpInstance",
            "dump-schemas = holland.backup.mysqlsh:MySqlShDumpSchemas",
        ]
    },
)
