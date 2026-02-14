from setuptools import find_namespace_packages, setup

version = "1.4.0"

setup(
    name="holland.backup.xtrabackup",
    version=version,
    description="Holland plugin for Percona XtraBackup",
    long_description="""\
      Holland plugin for Percona XtraBackup
      """,
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GPLv2",
    packages=find_namespace_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    include_package_data=True,
    zip_safe=True,
    test_suite="tests",
    install_requires=[],
    entry_points={
        "holland.backup": [
            "xtrabackup = holland.backup.xtrabackup:XtrabackupPlugin",
        ],
    },
)
