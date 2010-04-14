#!/bin/bash
OS=`uname`

echo "Platform: $OS"

shopt -s expand_aliases

CODE_BASE=$(cd $(dirname $0)/.. && pwd)
PLUGIN_ROOT=$CODE_BASE/plugins
ENV_ROOT="$HOME/holland-test"
HL_BACKPORTS="$CODE_BASE/holland-core/holland/core/backports/"
LOG="$ENV_ROOT/holland_install.log"
DEPOPTION=""

EASYINSTALL=""
for ei in easy_install easy_install-2.4 easy_install-2.5 easy_install-2.6
do
    which $ei > /dev/null 2>&1 
    if [ $? -eq 0 ]; then
        EASYINSTALL=$ei
        break
    fi
done

if [ "x${EASYINSTALL}" = "x" ]
then
    echo "python-setuptools appears missing, can't find easy_install"
    exit 1
else
    echo "Using easy_install = ${EASYINSTALL}"
fi

VIRTUALENV=""
for venv in virtualenv virtualenv-2.4 virtualenv-2.5 virtualenv2.6
do
    which $venv > /dev/null 2>&1 
    if [ $? -eq 0 ]; then
        VIRTUALENV=$venv
        break
    fi
done

if [ "x${VIRTUALENV}" = "x" ]
then
    echo "python-virtualenv could not be located."
    exit 1
else
    echo "Using virtualenv = ${VIRTUALENV}"
fi


# get options
for o in $@
do
    if [ $o = "--no-deps" ]; then
        DEPOPTIONS="--no-deps"
    fi
done

echo "Setting up Python Virtual Environment..."
rm -fr $ENV_ROOT
# use holland/core/backports to bootstrap virtualenv on 2.3
PYTHONPATH=$HL_BACKPORTS $VIRTUALENV $ENV_ROOT 
. $ENV_ROOT/bin/activate

# Installing some testing dependencies:
echo "Installing testing libs"
pushd $CODE_BASE/devtools/lib > /dev/null
    pushd 'mocker-0.10.1' > /dev/null
    printf "Installing mock-testing lib [mocker 0.10.1]..."
    python setup.py install >> $LOG
    if [ $? -eq 0 ]
    then
        echo -e "\033[32mOK\033[m"
    else
        echo -e "\033[31mFailed\033[m"
        exit 1
    fi
    popd > /dev/null
    pushd 'coverage-2.85' > /dev/null
    printf "Installing test-coverage lib [coverage 2.85]..."
    python setup.py install  >> $LOG
    if [ $? -eq 0 ]
    then
        echo -e "\033[32mOK\033[m"
    else
        echo -e "\033[31mFailed\033[m"
        exit 1
    fi
    popd > /dev/null
popd > /dev/null

echo -n "Installing Holland Core : "
cd $CODE_BASE/holland-core
python setup.py develop -q $DEPOPTIONS >> $LOG 2>&1
if [ $? -eq 0 ]
then
    echo -e "\033[32mOK\033[m"
else
    echo -e "\033[31mFailed\033[m"
    exit 1
fi

echo -n "Installing Holland Commvault : "
cd $CODE_BASE/addons/holland_commvault
python setup.py develop -q $DEPOPTIONS >> $LOG 2>&1
if [ $? -eq 0 ]
then
    echo -e "\033[32mOK\033[m"
else
    echo -e "\033[31mFailed\033[m"
fi

echo "Installing Holland Plugins"
mkdir -p $ENV_ROOT/usr/share/holland/plugins
cd $PLUGIN_ROOT
for name in $(cat ACTIVE)
do
    printf "\t%-30s : " $name
    cd $PLUGIN_ROOT/$name
    python setup.py develop $DEPOPTIONS >> $LOG 2>&1
    if [ $? -eq 0 ]
    then
        echo -e "\033[32mOK\033[m"
    else
        echo -e "\033[31mFailed\033[m"
    fi
done

echo "Install details available in $LOG"

mkdir -p $ENV_ROOT/etc/holland
cp -a $CODE_BASE/test_config/* $ENV_ROOT/etc/holland
# We don't use -i because this doesn't seem to be easily portable between 
# linux and freebsd
sed -e "s_env/_$ENV_ROOT/_g" \
    -e "s_holland.log_$ENV_ROOT/holland.log_" \
    < $ENV_ROOT/etc/holland/holland.conf > $ENV_ROOT/etc/holland/holland.conf.1
mv $ENV_ROOT/etc/holland/holland.conf.1 $ENV_ROOT/etc/holland/holland.conf

export HOLLAND_CONFIG="$ENV_ROOT/etc/holland/holland.conf"
cd $CODE_BASE
echo "Starting Shell"
$SHELL -i
