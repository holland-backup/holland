from setuptools import find_packages, setup

version = "1.2.12"

setup(
    name="holland",
    version=version,
    description="Holland Core Plugins",
    long_description="""\
      These are the plugins required for basic Holland functionality.
      """,
    classifiers=[],  # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    keywords="",
    author="Rackspace",
    author_email="holland-devel@googlegroups.com",
    url="http://www.hollandbackup.org/",
    license="3-Clause BSD",
    packages=find_packages(exclude=["ez_setup", "examples", "tests"]),
    include_package_data=True,
    zip_safe=True,
    test_suite="tests",
    install_requires=["configobj>=4.6.0", "setuptools"],
    entry_points={
        "console_scripts": [
            "holland = holland.core.cmdshell:main",
        ],
        "holland.commands": [
            "listplugins = holland.commands.list_plugins:ListPlugins",
            "listbackups = holland.commands.list_backups:ListBackups",
            "backup = holland.commands.backup:Backup",
            "mk-config = holland.commands.mk_config:MkConfig",
            "purge = holland.commands.purge:Purge",
        ],
    },
    namespace_packages=["holland"],
)
