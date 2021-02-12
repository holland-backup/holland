import os
import sys

from setuptools import find_packages, setup

version = "1.2.3"

setup(
    name="holland_commvault",
    version=version,
    description="Holland Addon for CommVault Support",
    long_description="""\
Commvault support command(s)""",
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="commvault holland backup",
    author="Rackspace",
    author_email="holland-coredev@lists.launchpad.net",
    license="3-Clause BSD",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=False,
    extras_require={"status_file": ["pid"]},
    entry_points={"console_scripts": ["holland_cvmysqlsv=holland_commvault:main"]},
)
