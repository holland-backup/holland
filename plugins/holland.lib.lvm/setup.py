from setuptools import find_namespace_packages, setup

version = "1.4.0"

setup(
    name="holland.lib.lvm",
    version=version,
    description="LVM support",
    long_description="""\
      """,
    keywords="holland lib lvm",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="GPLv2",
    packages=find_namespace_packages(exclude=["ez_setup", "examples", "tests", "tests.*"]),
    zip_safe=True,
)
