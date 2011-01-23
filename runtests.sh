#!/bin/sh
set -u
set -x
set -e

export PYLINTRC=$PWD/.pylintrc
nosetests -v --with-xunit
coverage=$(which coverage 2>/dev/null)
if [ $? -ne 0 ]
then
coverage=python-coverage
fi
$coverage xml
pylint -f parseable holland > pylint.txt
