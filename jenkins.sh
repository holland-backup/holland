#!/bin/sh
set -u
set -x

export TESTDIRS="tests/ \
                 plugins/holland.backup.random/tests/ \
                 plugins/holland.backup.sqlite/tests/"
python setup.py egg_info

export PYLINTRC=$PWD/.pylintrc
nosetests --with-coverage --cover-erase -v --with-xunit $TESTDIRS
which coverage > /dev/null 2>&1

if [ $? -ne 0 ]; then
    coverage='python-coverage'
else
    coverage='coverage'
fi
$coverage xml
export PYTHONPATH="$PWD/holland/cli/backports/"

pylint -f parseable holland > pylint.txt

exit 0
