PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE t1 (t1key INTEGER
                  PRIMARY KEY,data TEXT,num double,timeEnter DATE);
INSERT INTO "t1" VALUES(1,'This is sample data',3.0,NULL);
INSERT INTO "t1" VALUES(2,'More sample data',6.0,NULL);
INSERT INTO "t1" VALUES(3,'And a little more',9.0,NULL);
COMMIT;
