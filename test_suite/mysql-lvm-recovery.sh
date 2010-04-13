#!/bin/bash

echo "MySQL LVM Backup + InnoDB Recovery Test"
echo "Backing Up"
holland -q bk mysql-lvm-recovery
if [ $? -ne 0 ]
then
	echo "Backup Failed"
fi
echo "Dropping Tables"
mysql employees -e "SET FOREIGN_KEY_CHECKS = 0; DROP TABLE departments; DROP TABLE dept_manager; DROP TABLE salaries; DROP DATABASE world;"
echo "Restoring"
/etc/init.d/mysqld stop
BACKUP_DIR=`holland lb | grep "mysql-lvm-recovery" | awk -F/ {'print $2'} | tail -n1`
echo $BACKUP_DIR
tar -xzf /var/spool/holland/mysql-lvm-recovery/$BACKUP_DIR/backup.tar.gz -C /var/lib/mysql
/etc/init.d/mysqld start
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

