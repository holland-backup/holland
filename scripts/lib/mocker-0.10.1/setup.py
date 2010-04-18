#!/usr/bin/env python
import os
import re

try:
    from setuptools import setup, Extension
except ImportError:
    from distutils.core import setup, Extension


if os.path.isfile("MANIFEST"):
    os.unlink("MANIFEST")


version = re.search('__version__ = "([^"]+)"',
                    open("mocker.py").read()).group(1)

setup(
    name="mocker",
    version=version,
    description="Graceful platform for test doubles in Python (mocks, stubs, fakes, and dummies).",
    author="Gustavo Niemeyer",
    author_email="gustavo@niemeyer.net",
    license="PSF License",
    url="http://labix.org/mocker",
    download_url="https://launchpad.net/mocker/+download",
    py_modules=["mocker"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Python Software Foundation License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Testing",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
