#!/bin/sh
export PYLINTRC=$PWD/.pylintrc
nosetests -v --with-xunit
coverage xml
pylint -f parseable holland > pylint.txt
