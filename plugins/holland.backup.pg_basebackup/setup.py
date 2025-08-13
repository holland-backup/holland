from setuptools import find_packages, setup

version = "1.3.0"

setup(
    name="holland.backup.pg_basebackup",
    version=version,
    description="Holland pg_basebackup backup plugin",
    long_description="""\
      Postgres pg_basebackup backup""",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GNU GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    namespace_packages=["holland", "holland.backup"],
    zip_safe=True,
    install_requires=["psycopg2"],
    entry_points={
        "holland.backup": [
            "pg_basebackup = holland.backup.pg_basebackup:PgBaseBackup",
        ]
    },
)
