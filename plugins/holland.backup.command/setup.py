from setuptools import find_namespace_packages, setup

version = "1.4.0"

setup(
    name="holland.backup.command",
    version=version,
    description="Generic command backup plugin",
    long_description="""\
      Generic command backup plugin
      """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GPLv2",
    packages=find_namespace_packages(
        exclude=["ez_setup", "examples", "tests", "tests.*"]
    ),
    include_package_data=True,
    zip_safe=True,
    test_suite="tests",
    install_requires=[],
    entry_points={
        "holland.backup": [
            "command = holland.backup.command:CommandPlugin",
        ],
    },
)
