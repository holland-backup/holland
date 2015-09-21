Backup Providers
================

Here is an overview the providers included with Holland. For specific
configuration details on how to use these with a backup-set, see :doc:`config`

MySQL Providers
^^^^^^^^^^^^^^^

These providers are for backing up MySQL databases using various means. Since
there are so many providers specific to MySQL, these are given their own
section.

.. toctree::
    :maxdepth: 1

    provider_plugins/mysqldump
    provider_plugins/mysql-lvm
    provider_plugins/mysqldump-lvm
    provider_plugins/xtrabackup

Other Providers
^^^^^^^^^^^^^^^
These are providers which do something other than backup a MySQL database.

.. toctree::
    :maxdepth: 1

    provider_plugins/pgdump
    provider_plugins/rsync
    provider_plugins/example
