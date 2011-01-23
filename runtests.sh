#!/bin/sh
set -u
set -x
set -e

export PYLINTRC=$PWD/.pylintrc
nosetests -v --with-xunit tests
which coverage 2>&1 > /dev/null
if [ $? -ne 0 ]
then
coverage=python-coverage
else
coverage=coverage
fi
$coverage xml
pylint -f parseable holland > pylint.txt
