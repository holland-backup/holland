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
        apt-get -yq install python3-pip python3-psycopg2 python3-mysqldb rsync curl && \
        pip3 install configobj 'pylint>=2.17.0,<3.0.0' six 'pymongo>=3.6' && \
        python3 --version
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
        # Install MySQL
        export DEBIAN_FRONTEND=noninteractive && \
        apt-get -yq install mysql-server mysql-client || echo "Ignore errors"

        # Initialize MySQL
        rm -rf /var/lib/mysql/* && \
        mysqld --initialize-insecure --user=mysql 2>>/dev/null >>/dev/null

        # Start MySQL
        mysqld_safe --user=mysql 2>>/dev/null >>/dev/null &
        sleep 10
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
        mysqld_safe --user=mysql 2>>/dev/null >>/dev/null &
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
