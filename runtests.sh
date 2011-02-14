#!/bin/sh
set -u
set -x

python setup.py egg_info

export PYLINTRC=$PWD/.pylintrc
nosetests -v --with-xunit tests
which coverage > /dev/null 2>&1
if [ $? -ne 0 ]
then
coverage=python-coverage
else
coverage=coverage
fi
$coverage xml
pylint -f parseable holland > pylint.txt

exit 0
