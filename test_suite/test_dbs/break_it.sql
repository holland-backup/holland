DROP TABLE IF EXISTS `t1`;
DROP TABLE IF EXISTS `spaces in table`;
DROP TABLE IF EXISTS `underscores_in_table`;
DROP TABLE IF EXISTS `dashes-in-table`;
DROP TABLE IF EXISTS `symbols@$%^`;
DROP TABLE IF EXISTS `procedure`;

CREATE TABLE `t1` (num1 int) ENGINE='InnoDB';
CREATE TABLE `spaces in table` (num1 int) ENGINE='InnoDB';
CREATE TABLE `underscores_in_table` (num1 int) ENGINE='InnoDB';
CREATE TABLE `dashes-in-table` (num1 int) ENGINE='InnoDB';
CREATE TABLE `symbols@$%^` (num1 int) ENGINE='InnoDB';
CREATE TABLE `procedure` (num1 int) ENGINE='InnoDB';

INSERT INTO t1 VALUES (1);

INSERT INTO `spaces in table` SELECT * FROM t1;
INSERT INTO `underscores_in_table` SELECT * FROM t1;
INSERT INTO `spaces in table` SELECT * FROM t1;
INSERT INTO `dashes-in-table` SELECT * FROM t1;
INSERT INTO `symbols@$%^` SELECT * FROM t1;
INSERT INTO `procedure` SELECT * FROM t1;
