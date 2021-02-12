#!/bin/bash

source ~/virtualenv/python${TRAVIS_PYTHON_VERSION}/bin/activate

# Begin Pylint
pylint ./holland/

pylint_failed=0
for d in $(ls -d ./plugins/*/holland ./contrib/holland-commvault/holland_commvault)
do
    pylint $d
    if [ $? -ne 0 ] && [ $pylint_failed -ne 1 ]
    then
        pylint_failed=1
    fi
done
if [ $pylint_failed -ne 0 ]
then
    echo "Pylint failed; please review above output."
    exit $pylint_failed
fi
# End Pylint

for i in `ls -d plugins/holland.*`
do
    cd $TRAVIS_BUILD_DIR/${i}
    python setup.py install
    exit_code=$?
	if [ $exit_code -ne 0 ]
    then
        echo "Failed installing $i"
        exit $exit_code
    fi
done

cd $TRAVIS_BUILD_DIR/contrib/holland-commvault/
python setup.py install
exit_code=$?
if [ $exit_code -ne 0 ]
then
    echo "Failed installing holland_commvault"
    exit $exit_code
fi

mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
cp $TRAVIS_BUILD_DIR/config/holland.conf /etc/holland/
cp $TRAVIS_BUILD_DIR/config/providers/* /etc/holland/providers/


# Work around if xtrabackup hasn't released a new version
echo "holland mc --name xtrabackup xtrabackup"
sleep 1
holland mc --name xtrabackup xtrabackup
exit_code=$?
sed -i 's/additional-options = ,/additional-options = "--no-server-version-check",/g' /etc/holland/backupsets/xtrabackup.conf
if [ $exit_code -ne  0 ]
then
    echo "Failed running holland mc xtrabackup"
    exit $exit_code
fi

CMDS=(
"holland mc --name mysqldump mysqldump"
"holland mc -f /tmp/mysqldump.conf mysqldump"
"holland bk mysqldump --dry-run"
"holland bk mysqldump"
"holland mc --file /tmp/xtrabackup.conf xtrabackup"
"holland bk xtrabackup --dry-run"
"holland bk xtrabackup"
"holland mc --name mongodump mongodump"
"holland mc --file /tmp/mongodump.conf mongodump"
"holland bk mongodump --dry-run"
"holland bk mongodump"
"holland bk mysqldump xtrabackup"
"holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001 --bkset mysqldump"
"holland mc --name default mysqldump"
"holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001"
)

for command in "${CMDS[@]}"
do
    echo $command
    sleep 1
    $command
    exit_code=$?
	if [ $exit_code -ne  0 ]
    then
        echo "Failed running $command"
        exit $exit_code
    fi
done

# Stopgap measure to check for issue 213
sed -i 's|^estimate-method = plugin$|estimate-method = const:1K|' /etc/holland/backupsets/mysqldump.conf
echo "holland bk mysqldump"
sleep 1
holland bk mysqldump
exit_code=$?
if [ $exit_code -ne  0 ]
then
    echo "Failed running holland bk mysqldump with constant estimate size"
    exit $exit_code
fi

# test that split command is working as expected
sed -i 's|^split = no|split = yes|' /etc/holland/backupsets/mysqldump.conf
echo "holland bk mysqldump"
sleep 1
holland bk mysqldump
exit_code=$?
if [ $exit_code -ne  0 ]
then
    echo "Failed running holland bk mysqldump with constant estimate size"
    exit $exit_code
fi
exit 0
