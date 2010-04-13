#!/bin/bash
echo "Table Filtering Restore Test - mysqldump"
echo "Backing Up"
holland -q bk mysqldump-table-filtering
if [ $? -ne 0 ]
then
	echo "Backup Failed"
fi
echo "Dropping Tables"
mysql employees -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE departments; DROP TABLE dept_manager; DROP TABLE salaries;"
echo "Restoring"
BACKUP_DIR=`holland lb | grep "mysqldump-table-filtering" | awk -F/ {'print $2'} | tail -n1`
echo $BACKUP_DIR
zcat /var/spool/holland/mysqldump-table-filtering/$BACKUP_DIR/backup_data/employees.sql.gz | mysql
echo "Re-running mk-table-checksum to Compare"
mk-table-checksum --checksum localhost > mk-checksum-after
echo "Comparing checksums"
diff mk-checksum-before mk-checksum-after 1> /dev/null
if [ $? -ne 0 ]
then
	echo "Test FAILED!"
else
	echo "Test PASSED!"
fi
