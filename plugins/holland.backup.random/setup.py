from setuptools import find_packages, setup

version = "1.2.10"

setup(
    name="holland.backup.random",
    version=version,
    description="Back up data from /dev/random",
    long_description="""\
      Uses /dev/random. A bit more of an example then holland.backup.example
      """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="random",
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
      random = holland.backup.random:RandomPlugin
      """,
    namespace_packages=["holland", "holland.backup"],
)
