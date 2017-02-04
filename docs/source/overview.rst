Usage and Implementation Overview
=================================

Holland is built around the concept of plugins, though for the end user, most
of these plugins will be in the form of backup providers and their helper
plugins. These are configured by way of a backup-set which defines the
characteristics of a particular backup.

.. _overview-providers:

Provider Plugins
^^^^^^^^^^^^^^^^

Provider plugins provide a backup service for use in a backup set. They
are the interface between Holland and the method of backing up data.

As Holland is a framework, it can actually backup most anything as long
as there is a provider plugin for it. The idea is to present an easy to use
and clear method of backing up and restoring backups no matter the source.

Backup-Sets
^^^^^^^^^^^
A backup-set is compromised of global, provider, and helper plugin
configuration options which make up a particular backup. These options are
stored in a simple INI-based configuration file. The name of the configuration
file corresponds to the name of the backup set.

For instance, once might want to backup a handful of MySQL databases using
some specific mysqldump settings; while backing up another set of MySQL
databases using different settings. To do this, one might create two backups
sets for each scenario.

Most plugins come with a set of defaults such that only values that need to be
overridden need to be specified in a backup-set if desired. Such defaults
can be modified on a global basis by editing the global provider configuration
files (see :ref:`overview-providers`).

Backups
^^^^^^^
Backups are of course the end product of the whole exercise. Holland stores
these under the ``backup_direcotry`` defined in the main ``holland.conf``
configuration file. The default location is usually ``/var/spool/holland``.
Under this directory there is a sub-directory for individual backup-sets.
Under those directories are the actual backup directories. The name of each
backup directory is the timestamp of when it was run. As of Holland 1.0.8
or newer, there are also ``newest`` and ``oldest`` directories which,
perhaps unsurprisingly, correspond to the newest and oldest backup.

As implied, there can be multiple backups under a backup-set. The scheduling
of running backups is up to you. Holland does not care how often backups are
run - it only cares about how many backups to keep. This, with the help of
services like ``cron``, one can be fairly flexible about the scheduling and
frequency of backups.
