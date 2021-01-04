from setuptools import setup, find_packages
import sys, os

version = "1.1.22"
if sys.version_info[0] == 2 and sys.version_info[1] < 7:
    install_requires = (["psycopg2<2.7.7"],)
else:
    install_requires = (["psycopg2"],)

setup(
    name="holland.backup.pgdump",
    version=version,
    description="Holland pg_dump backup plugin",
    long_description="""\
      Postgres pg_dump backup""",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="https://gforge.rackspace.com/gf/project/holland",
    license="GNU GPLv2",
    packages=find_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    namespace_packages=["holland", "holland.backup"],
    zip_safe=True,
    install_requires=install_requires,
    # holland looks for plugins in holland.backup
    entry_points="""
      [holland.backup]
      pgdump = holland.backup.pgdump:PgDump
      """,
)
