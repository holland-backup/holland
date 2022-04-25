from setuptools import find_packages, setup

version = "1.2.10"

setup(
    name="holland.backup.tar",
    version=version,
    description="Tar Plugin for Holland",
    long_description="""\
      Tar plugin for the Holland backup framework
      """,
    author="Cashstar",
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
      tar = holland.backup.tar:TarPlugin
      """,
    namespace_packages=["holland", "holland.backup"],
)
