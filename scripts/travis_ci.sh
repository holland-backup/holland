#!/bin/bash -x


for i in `ls -d plugins/holland.*`
do
    cd ${i}
    python setup.py install 2>>/dev/null >>/dev/null
    exit_code=$?
	if [ $exit_code -ne  0 ]
    then
        echo "Failed installing $i"
        exit $exit_code
    fi
done
mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
cp /holland/config/holland.conf /etc/holland/
cp /holland/config/providers/* /etc/holland/providers/


CMDS=(
"holland mc --name mysqldump mysqldump"
"holland bk mysqldump --dry-run"
"holland bk mysqldump"
"holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001 --bkset mysqldump"
)

for command in "${CMDS[@]}"
do
    $command 2>>/dev/null >>/dev/null
    exit_code=$?
	if [ $exit_code -ne  0 ]
    then
        echo "Failed running $i"
        exit $exit_code
    fi
done
exit 0
