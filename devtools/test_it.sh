#!/bin/sh

BASE=$PWD
PLUGIN_ROOT=$BASE/plugins
ENV_ROOT=$PWD/env

echo "Setting up Python Virtual environment for testing"
echo "Setting up Python Virtual Environment"
rm -fr $ENV_ROOT
virtualenv $ENV_ROOT
. $ENV_ROOT/bin/activate

echo -n "Testing holland-core... "
cd $BASE/holland-core
echo "------- Testing holland-core --------" >> $BASE/test.log
python setup.py test >> $BASE/test.log 2>&1
if [ $? -eq 0 ]
then
    echo -e "\033[32mOK\033[m"
else
    echo -e "\033[31Failed\033[m"
    exit 1
fi
# Install holland in virtual env for testing plugins
echo "------ Installing Holland --------" >> $BASE/test.log
python setup.py develop >> $BASE/test.log 2>&1

echo "Installing Holland Plugins into Dev environment"
cd $PLUGIN_ROOT
for name in holland*
do
    printf "\t%-30s : " $name
    cd $PLUGIN_ROOT/$name
    echo "------- Installing Plugin $name --------" >> $BASE/test.log
    python setup.py install >> $BASE/test.log 2>&1
    if [ $? -eq 0 ]
    then
        echo -e "\033[32mOK\033[m"
    else
        echo -e "\033[31mFailed\033[m"
    fi
done

echo "Testing Holland Plugins"
cd $PLUGIN_ROOT
for name in holland*
do
    printf "\t%-30s : " $name
    cd $PLUGIN_ROOT/$name
    echo "------- Testing Plugin $name --------" >> $BASE/test.log
    python setup.py test >> $BASE/test.log 2>&1
    if [ $? -eq 0 ]
    then
        echo -e "\033[32mOK\033[m"
    else
        echo -e "\033[31mFailed\033[m"
    fi
done

rm -fr $ENV_ROOT
