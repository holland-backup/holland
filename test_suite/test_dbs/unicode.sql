-- MySQL dump 10.13  Distrib 5.1.40, for apple-darwin10.0.0 (i386)
--
-- Host: localhost    Database: נעטהערלאַנדס
-- ------------------------------------------------------
-- Server version	5.1.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Current Database: `נעטהערלאַנדס`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `נעטהערלאַנדס` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `נעטהערלאַנדס`;

--
-- Table structure for table `נעטהערלאַנדס`
--

DROP TABLE IF EXISTS `נעטהערלאַנדס`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `נעטהערלאַנדס` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Yiddish';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `נעטהערלאַנדס`
--

LOCK TABLES `נעטהערלאַנדס` WRITE;
/*!40000 ALTER TABLE `נעטהערלאַנדס` DISABLE KEYS */;
/*!40000 ALTER TABLE `נעטהערלאַנדס` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `هلند`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `هلند` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `هلند`;

--
-- Table structure for table `هلند`
--

DROP TABLE IF EXISTS `هلند`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `هلند` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Persian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `هلند`
--

LOCK TABLES `هلند` WRITE;
/*!40000 ALTER TABLE `هلند` DISABLE KEYS */;
/*!40000 ALTER TABLE `هلند` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `هولندا`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `هولندا` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `هولندا`;

--
-- Table structure for table `هولندا`
--

DROP TABLE IF EXISTS `هولندا`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `هولندا` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='ARABIC';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `هولندا`
--

LOCK TABLES `هولندا` WRITE;
/*!40000 ALTER TABLE `هولندا` DISABLE KEYS */;
/*!40000 ALTER TABLE `هولندا` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `नीदरलैण्ड`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `नीदरलैण्ड` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `नीदरलैण्ड`;

--
-- Table structure for table `नीदरलैण्ड`
--

DROP TABLE IF EXISTS `नीदरलैण्ड`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `नीदरलैण्ड` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Hindi';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `नीदरलैण्ड`
--

LOCK TABLES `नीदरलैण्ड` WRITE;
/*!40000 ALTER TABLE `नीदरलैण्ड` DISABLE KEYS */;
/*!40000 ALTER TABLE `नीदरलैण्ड` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `เนเธอร์แลนด์`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `เนเธอร์แลนด์` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `เนเธอร์แลนด์`;

--
-- Table structure for table `เนเธอร์แลนด์`
--

DROP TABLE IF EXISTS `เนเธอร์แลนด์`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `เนเธอร์แลนด์` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Thai';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `เนเธอร์แลนด์`
--

LOCK TABLES `เนเธอร์แลนด์` WRITE;
/*!40000 ALTER TABLE `เนเธอร์แลนด์` DISABLE KEYS */;
/*!40000 ALTER TABLE `เนเธอร์แลนด์` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `オラ`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `オラ` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `オラ`;

--
-- Table structure for table `オラ`
--

DROP TABLE IF EXISTS `オラ`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `オラ` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Japanese';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `オラ`
--

LOCK TABLES `オラ` WRITE;
/*!40000 ALTER TABLE `オラ` DISABLE KEYS */;
/*!40000 ALTER TABLE `オラ` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Ολλανδία`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `ολλανδία` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Ολλανδία`;

--
-- Table structure for table `Ολλανδία`
--

DROP TABLE IF EXISTS `Ολλανδία`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Ολλανδία` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Greek';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Ολλανδία`
--

LOCK TABLES `Ολλανδία` WRITE;
/*!40000 ALTER TABLE `Ολλανδία` DISABLE KEYS */;
/*!40000 ALTER TABLE `Ολλανδία` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `荷兰`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `荷兰` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `荷兰`;

--
-- Table structure for table `荷兰`
--

DROP TABLE IF EXISTS `荷兰`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `荷兰` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Chinese simplified';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `荷兰`
--

LOCK TABLES `荷兰` WRITE;
/*!40000 ALTER TABLE `荷兰` DISABLE KEYS */;
/*!40000 ALTER TABLE `荷兰` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `荷蘭`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `荷蘭` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `荷蘭`;

--
-- Table structure for table `荷蘭`
--

DROP TABLE IF EXISTS `荷蘭`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `荷蘭` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Chinese traditional';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `荷蘭`
--

LOCK TABLES `荷蘭` WRITE;
/*!40000 ALTER TABLE `荷蘭` DISABLE KEYS */;
/*!40000 ALTER TABLE `荷蘭` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Холандија`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `холандија` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Холандија`;

--
-- Table structure for table `Холандија`
--

DROP TABLE IF EXISTS `Холандија`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Холандија` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Macedonian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Холандија`
--

LOCK TABLES `Холандија` WRITE;
/*!40000 ALTER TABLE `Холандија` DISABLE KEYS */;
/*!40000 ALTER TABLE `Холандија` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Холандия`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `холандия` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Холандия`;

--
-- Table structure for table `Холандия`
--

DROP TABLE IF EXISTS `Холандия`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Холандия` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Bulgarian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Холандия`
--

LOCK TABLES `Холандия` WRITE;
/*!40000 ALTER TABLE `Холандия` DISABLE KEYS */;
/*!40000 ALTER TABLE `Холандия` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Голландия`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `голландия` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Голландия`;

--
-- Table structure for table `Голландия`
--

DROP TABLE IF EXISTS `Голландия`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Голландия` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Russian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Голландия`
--

LOCK TABLES `Голландия` WRITE;
/*!40000 ALTER TABLE `Голландия` DISABLE KEYS */;
/*!40000 ALTER TABLE `Голландия` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Нідерланди`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `нідерланди` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Нідерланди`;

--
-- Table structure for table `Нідерланди`
--

DROP TABLE IF EXISTS `Нідерланди`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Нідерланди` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Ukrainian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Нідерланди`
--

LOCK TABLES `Нідерланди` WRITE;
/*!40000 ALTER TABLE `Нідерланди` DISABLE KEYS */;
/*!40000 ALTER TABLE `Нідерланди` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `네덜란드`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `네덜란드` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `네덜란드`;

--
-- Table structure for table `네덜란드`
--

DROP TABLE IF EXISTS `네덜란드`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `네덜란드` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Korean';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `네덜란드`
--

LOCK TABLES `네덜란드` WRITE;
/*!40000 ALTER TABLE `네덜란드` DISABLE KEYS */;
/*!40000 ALTER TABLE `네덜란드` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Alankomaat`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `alankomaat` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Alankomaat`;

--
-- Table structure for table `Alankomaat`
--

DROP TABLE IF EXISTS `Alankomaat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Alankomaat` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Finnish';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Alankomaat`
--

LOCK TABLES `Alankomaat` WRITE;
/*!40000 ALTER TABLE `Alankomaat` DISABLE KEYS */;
/*!40000 ALTER TABLE `Alankomaat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Holland`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `holland` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Holland`;

--
-- Table structure for table `Holland`
--

DROP TABLE IF EXISTS `Holland`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Holland` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='English';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Holland`
--

LOCK TABLES `Holland` WRITE;
/*!40000 ALTER TABLE `Holland` DISABLE KEYS */;
/*!40000 ALTER TABLE `Holland` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Nīderlande`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `nīderlande` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Nīderlande`;

--
-- Table structure for table `Nīderlande`
--

DROP TABLE IF EXISTS `Nīderlande`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Nīderlande` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Latvian';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Nīderlande`
--

LOCK TABLES `Nīderlande` WRITE;
/*!40000 ALTER TABLE `Nīderlande` DISABLE KEYS */;
/*!40000 ALTER TABLE `Nīderlande` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Nederländerna`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `nederländerna` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Nederländerna`;

--
-- Table structure for table `Nederländerna`
--

DROP TABLE IF EXISTS `Nederländerna`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Nederländerna` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Swedish';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Nederländerna`
--

LOCK TABLES `Nederländerna` WRITE;
/*!40000 ALTER TABLE `Nederländerna` DISABLE KEYS */;
/*!40000 ALTER TABLE `Nederländerna` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Nederland`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `nederland` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Nederland`;

--
-- Table structure for table `Nederland`
--

DROP TABLE IF EXISTS `Nederland`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Nederland` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Dutch';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Nederland`
--

LOCK TABLES `Nederland` WRITE;
/*!40000 ALTER TABLE `Nederland` DISABLE KEYS */;
/*!40000 ALTER TABLE `Nederland` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `Niðurlönd`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `niðurlönd` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `Niðurlönd`;

--
-- Table structure for table `Niðurlönd`
--

DROP TABLE IF EXISTS `Niðurlönd`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `Niðurlönd` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Icelandic';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Niðurlönd`
--

LOCK TABLES `Niðurlönd` WRITE;
/*!40000 ALTER TABLE `Niðurlönd` DISABLE KEYS */;
/*!40000 ALTER TABLE `Niðurlönd` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Current Database: `nước`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `nước` /*!40100 DEFAULT CHARACTER SET utf8 */;

USE `nước`;

--
-- Table structure for table `nước`
--

DROP TABLE IF EXISTS `nước`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8 */;
CREATE TABLE `nước` (
  `id` int(10) unsigned NOT NULL,
  `data` text,
  PRIMARY KEY (`id`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8 COMMENT='Vietnamese';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `nước`
--

LOCK TABLES `nước` WRITE;
/*!40000 ALTER TABLE `nước` DISABLE KEYS */;
/*!40000 ALTER TABLE `nước` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2009-11-17 18:11:47
