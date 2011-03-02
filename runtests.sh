#!/bin/sh
set -u
set -x

python setup.py egg_info
nosetests -v tests
