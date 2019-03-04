#!/bin/bash

source ~/virtualenv/python${TRAVIS_PYTHON_VERSION}/bin/activate

# Begin Pylint
if [[ $TRAVIS_PYTHON_VERSION != '2.6' ]]
then
    pylint ./holland/
fi

if [[ $TRAVIS_PYTHON_VERSION != '2.6' ]]
then
    pylint_failed=0
    for d in $(ls -d ./plugins/*/holland ./contrib/holland-commvault/holland_commvault)
    do
        pylint $d
        if [ $? -ne 0 ] && [ $pylint_failed -ne 1 ]
        then
            pylint_failed=1
        fi
    done
fi

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
	if [ $exit_code -ne  0 ]
    then
        echo "Failed installing $i"
        exit $exit_code
    fi
done

cd $TRAVIS_BUILD_DIR/contrib/holland-commvault/
python setup.py install
exit_code=$?
if [ $exit_code -ne  0 ]
then
    echo "Failed installing holland_commvault"
    exit $exit_code
fi

mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
cp $TRAVIS_BUILD_DIR/config/holland.conf /etc/holland/
cp $TRAVIS_BUILD_DIR/config/providers/* /etc/holland/providers/

echo 'host all root 127.0.0.1/32 trust' >> /var/lib/pgsql/data/pg_hba.conf
su -c 'psql -c "CREATE USER root WITH SUPERUSER"' postgres

CMDS=(
"holland mc --name mysqldump mysqldump"
"holland mc -f /tmp/mysqldump.conf mysqldump"
"holland bk mysqldump --dry-run"
"holland bk mysqldump"
"holland mc --name xtrabackup xtrabackup"
"holland mc --file /tmp/xtrabackup.conf xtrabackup"
"holland bk xtrabackup --dry-run"
"holland bk xtrabackup"
"holland mc --name mongodump mongodump"
"holland mc --file /tmp/mongodump.conf mongodump"
"holland bk mongodump --dry-run"
"holland bk mongodump"
"holland mc --name pgdump pgdump"
"holland mc --file /tmp/pgdump.conf pgdump"
"holland bk pgdump --dry-run"
"holland bk pgdump"
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
sleep 1
holland bk mysqldump
exit_code=$?
if [ $exit_code -ne  0 ]
then
    echo "Failed running holland bk mysqldump with constant estimate size"
    exit $exit_code
fi
exit 0
