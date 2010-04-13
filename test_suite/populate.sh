#!/bin/bash

EMPLOYEES_VER="1.0.6"

cd test_dbs

echo "Importing world"
mysql -e "drop database if exists world"
mysql -e "create database world"
zcat world.sql.gz | mysql world

echo "Importing employees_db"
tar -xvjf employees_db-full-$EMPLOYEES_VER.tar.bz2 
cd employees_db
mysql -t < employees.sql
cd ..

echo "Importing sakila"
tar -xvzf sakila-db.tar.gz
cd sakila-db
mysql < sakila-schema.sql
mysql < sakila-data.sql
cd ..

echo "Importing menagerie"
tar -xvzf menagerie-db.tar.gz
cd menagerie-db
mysql -e "drop database if exists menagerie"
mysql -e "create database menagerie"
mysql menagerie -e "SOURCE cr_pet_tbl.sql"
mysql menagerie -e "LOAD DATA LOCAL INFILE 'pet.txt' INTO TABLE pet"
mysql menagerie -e "SOURCE ins_puff_rec.sql"
mysql menagerie -e "SOURCE cr_event_tbl.sql"
mysql menagerie -e "LOAD DATA LOCAL INFILE 'event.txt' INTO TABLE event"
cd ..

cd ..
