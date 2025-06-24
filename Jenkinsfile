pipeline {
  agent {
    docker {
      image 'ubuntu'
      args '-u root:root'
    }

  }
  stages {
    stage('Install General Dependencies') {
      steps {
        sh '''
        # Install packages
        apt-get update && \
        apt-get -yq install python3-pip python3-psycopg2 python3-mysqldb rsync curl wget lsb-release gnupg2 locales && \
        pip3 install configobj 'pylint>=2.17.0,<3.0.0' six 'pymongo>=3.6' && \
        python3 --version
        locale-gen en_US.UTF-8
        '''
      }
    }
    stage('Display OS Info') {
      steps {
        sh 'cat /etc/os-release'
      }
    }
    stage('Install Holland') {
      steps {
        sh '''
        # Move over to tmp to prevent file permissions issues
        mkdir -p /tmp/holland
        rsync -art $WORKSPACE/ /tmp/holland/
        cd /tmp/holland

        # Install Holland
        python3 setup.py install

        # Install Plugins
        for i in `ls -d plugins/holland.*`
        do
            cd /tmp/holland/${i}
            python3 setup.py install
            exit_code=$?
            if [ $exit_code -ne 0 ]
            then
                echo "Failed installing $i"
                exit $exit_code
            fi
        done

        # Create Holland directories and copy configs
        mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
        cp ${WORKSPACE}/config/holland.conf /etc/holland/
        cp ${WORKSPACE}/config/providers/* /etc/holland/providers/
        '''
      }
    }
    stage('Pylint Holland and Plugins') {
      parallel {
        stage('Pylint Holland') {
          steps {
            sh 'pylint holland'
          }
        }
        stage('Pylint Plugins') {
          steps {
            sh '''
            pylint_failed=0
            for d in $(ls -d ./plugins/*/holland ./contrib/holland-commvault/holland_commvault)
            do
                echo $d
                pylint $d
                if [ $? -ne 0 ] && [ $pylint_failed -ne 1 ]
                then
                    pylint_failed=1
                fi
            done
            if [ $pylint_failed -ne 0 ]
            then
                echo "Pylint failed; please review above output."
                exit $pylint_failed
            fi
            '''
          }
        }
      }
    }
    stage('Setup MySQL Database') {
      steps {
        sh '''
        export DEBIAN_FRONTEND=noninteractive

        # Try to prevent mysql from starting automatically
        echo 'exit 101' > /usr/sbin/policy-rc.d && chmod +x /usr/sbin/policy-rc.d

        # Using community repo to simplify installation of mysql-shell
        wget https://dev.mysql.com/get/mysql-apt-config_0.8.29-1_all.deb
        echo "mysql-apt-config mysql-apt-config/select-server select mysql-8.0" | debconf-set-selections
        echo "mysql-apt-config mysql-apt-config/select-tools select Enabled" | debconf-set-selections
        dpkg -i mysql-apt-config_0.8.29-1_all.deb

        # Install mysql-server and mysql-shell
        apt-get update && \
        apt-get -yq install mysql-server mysql-shell

        # Initialize MySQL
        rm -rf /var/lib/mysql/* && \
        mysqld --initialize-insecure --user=mysql > /dev/null 2>&1

        # Start MySQL
        mysqld_safe --user=mysql > /dev/null 2>&1 &
        sleep 10

        # Download and extract Sakila database
        wget -q https://downloads.mysql.com/docs/sakila-db.tar.gz -O /tmp/sakila-db.tar.gz && \
        tar -xzf /tmp/sakila-db.tar.gz -C /tmp && \
        rm /tmp/sakila-db.tar.gz

        # Populate MySQL with Sakila database
        mysql -e "SOURCE /tmp/sakila-db/sakila-schema.sql;" && \
        mysql -e "SOURCE /tmp/sakila-db/sakila-data.sql;"
        '''
      }
    }
    stage('Test Holland Command Plugin') {
      steps {
        sh '''
        # Test holland bk dump-instance --dry-run
        holland mc --name command command

        # Set command setting in backupset config
        sed -i 's|# command = "" # no default|command = rsync -av /var/lib/mysql {backup_data_dir}|' /etc/holland/backupsets/command.conf

        # Test holland bk command --dry-run
        holland bk command --dry-run

        # Test holland bk command
        holland bk command
        '''
      }
    }
    stage('Test Holland with MySQL') {
      steps {
        sh '''

        # Test holland mc -f
        holland mc -f /tmp/mysqldump.conf mysqldump

        # Create a mysqldump backupset
        holland mc --name mysqldump mysqldump

        # Test holland bk mysqldump --dry-run
        holland bk mysqldump --dry-run

        # Test holland bk mysqldump
        holland bk mysqldump

        # Test to check for https://github.com/holland-backup/holland/issues/213
        sed -i \'s|^estimate-method = plugin$|estimate-method = const:1K|\' /etc/holland/backupsets/mysqldump.conf
        holland bk mysqldump

        # Test that split command is working as expected
        sed -i \'s|^split = no|split = yes|\' /etc/holland/backupsets/mysqldump.conf
        holland bk mysqldump

        # Create mysqlsh backupsets
        holland mc --name mysqlsh-dump-instance mysqlsh-dump-instance
        holland mc --name mysqlsh-dump-schemas mysqlsh-dump-schemas

        # Specify the schemas to dump for dump-schemas
        sed -i 's/schemas = /schemas = mysql,sakila/' /etc/holland/backupsets/mysqlsh-dump-schemas.conf

        # Create .my.cnf file for root user. This is needed for mysqlsh to work properly here in
        # this pipelline.
        printf '[client]\nuser=root\npassword=\nsocket=/var/run/mysqld/mysqld.sock\n' > ~/.my.cnf
        chmod 600 ~/.my.cnf

        # Test holland bk mysqlsh-dump-instance --dry-run
        holland bk mysqlsh-dump-instance --dry-run

        # Test holland bk mysqlsh-dump-instance
        holland bk mysqlsh-dump-instance

        # Test holland bk mysqlsh-dump-schemas --dry-run
        holland bk mysqlsh-dump-schemas --dry-run

        # Test holland bk mysqlsh-dump-schemas
        holland bk mysqlsh-dump-schemas

        # Remove .my.cnf file
        rm ~/.my.cnf
        '''
      }
    }
    stage('Swap to MariaDB 10.11') {
      steps {
        sh '''
        # Stop Running MySQL instance
        mysqladmin shutdown

        # Remove MySQL packages
        rm -rf /etc/mysql /var/lib/mysql /var/log/mysql /var/run/mysqld && \
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get -yq remove --purge mysql-server mysql-client mysql-common && \
        apt-get -yq autoremove && \
        apt-get -yq remove dbconfig-mysql

        # Install MariaDB 10.11
        curl -LsS https://r.mariadb.com/downloads/mariadb_repo_setup | bash -s -- --mariadb-server-version=mariadb-10.11 && \
        apt-get update && \
        apt-get -yq install mariadb-server mariadb-client

        # Initialize MariaDB
        rm -rf /var/lib/mysql && \
        mysql_install_db --user=mysql --datadir=/var/lib/mysql --auth-root-authentication-method=normal

        # Start MariaDB
        mysqld_safe --user=mysql > /dev/null 2>&1 &
        sleep 10
        '''
      }
    }
    stage('Test Holland with MariaDB') {
      steps {
        sh '''
        # Create a maridb-dump backupset
        holland mc --name mariadb-dump mariadb-dump

        # Test holland bk maridb-dump --dry-run
        holland bk mariadb-dump --dry-run

        # Test holland bk maridb-dump
        holland bk mariadb-dump
        '''
      }
    }

  }
}
