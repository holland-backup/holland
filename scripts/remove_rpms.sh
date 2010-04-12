#!/bin/bash
#
# This script removes the common Holland RPMs to make it easy to 
# install/uninstall for testing purposes. Do not expect it to 
# work flawlessly :) In fact, this shoudl be replaced by 
# a sane way of doing this.
#
rpm -e holland holland-common holland-example holland-maatkit \
holland-mysqldump holland-mysqlhotcopy holland-mysqllvm
