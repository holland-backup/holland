#!/bin/bash

source ~/virtualenv/python${TRAVIS_PYTHON_VERSION}/bin/activate

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


CMDS=(
"holland mc --name mysqldump mysqldump"
"holland bk mysqldump --dry-run"
"holland bk mysqldump"
"holland mc --name xtrabackup xtrabackup"
"holland bk xtrabackup --dry-run"
"holland bk xtrabackup"
"holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001 --bkset mysqldump"
)

for command in "${CMDS[@]}"
do
    sleep 1
    $command
    exit_code=$?
	if [ $exit_code -ne  0 ]
    then
        echo "Failed running $command"
        exit $exit_code
    fi
done
exit 0
