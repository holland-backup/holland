[mysqld]
********

**mysqld-exe** = path

    Path to the MySQL binary. By default, ``mysqld`` or ``/usr/libexec/mysqld``
    is used.

**user** = user

    User to run the MySQL bootstrapped instance as. By default ``mysql`` is used.

**innodb-buffer-pool-size** = #M

    The size to set the innodb buffer pool of the bootstrapped instance.
    The default is 128M. If there is additional RAM available on the server,
    setting this higher will improve the total backup time. Be mindful not to
    set this too high to avoid starving the system of RAM.

**key-buffer-size** = #M

    The size to set the key buffer of the bootstrapped instance. The default
    is 8M. Setting this higher can improve backup performance (though less
    significantly than the ``innodb-buffer-pool-size``. Be mindful not to
    set this too high to avoid straving the system of RAM.

    This setting is only useful with the ``mysqldump-lvm`` provider.

**tmpdir** = path

    The location to use for the tmpdir of the bootstrapped instance, with
    the default being the default for MySQL.

