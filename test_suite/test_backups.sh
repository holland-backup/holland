#!/bin/bash

echo "Running mk-table-checksum for a Bassline"
mk-table-checksum --checksum localhost > mk-checksum-before

#source mysqldump-table-filtering.sh
source mysql-lvm-recovery.sh

