make_sandbox \
/home/tim/opt/mysql/5.1.46/mysql-5.1.46-linux-x86_64-glibc23.tar.gz \
--upper_directory=$PWD/sandbox \
--sandbox_directory=mysql \
--sandbox_port=3399 \
--datadir_from=dir:/home/tim/opt/mysql/mysql-datadir \
--db_user=root \
--db_password=password \
--no_confirm 


