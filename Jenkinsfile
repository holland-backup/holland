pipeline {
  agent {
    docker {
      image 'ubuntu'
      args '-u root:root'
    }

  }
  stages {
    stage('Setup Env') {
      steps {
        sh '''apt-get update
apt-get install -y python3-pip python3-psycopg2 rsync
pip3 install configobj
pip3 install pylint
pip3 install six
python3 --version'''
      }
    }

    stage('pylint holland') {
      parallel {
        stage('pylint holland') {
          steps {
            sh '''pylint holland

'''
          }
        }


      }
    }

    stage('Install holland') {
      steps {
        sh '''# Move over to tmp to prevent file permissions issues
mkdir -p /tmp/holland
rsync -art $WORKSPACE/ /tmp/holland/
cd /tmp/holland

# Install Holland
python3 setup.py install


# Install Commvault script
cd /tmp/holland/contrib/holland-commvault/
python3 setup.py install'''
      }
    }

    stage('pylint plugins') {
          steps {
            sh '''pylint_failed=0
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
fi'''
          }
        }
    stage('Install plugins') {
          steps {
            sh '''
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
done'''
          }
        }

    stage('Setup holland') {
      parallel {
        stage('Setup holland') {
          steps {
            sh '''mkdir -p /etc/holland/providers /etc/holland/backupsets /var/log/holland /var/spool/holland
cp ${WORKSPACE}/config/holland.conf /etc/holland/
cp ${WORKSPACE}/config/providers/* /etc/holland/providers/
'''
          }
        }

        stage('Setup Database') {
          steps {
            sh '''DEBIAN_FRONTEND=noninteractive apt-get -yq install mysql-server python3-mysqldb|| echo "Ignore errors"

mkdir -p /var/log/mysql/
touch /var/log/mysql/error.log
chown -R mysql:mysql /var/log/mysql

rm -rf /var/lib/mysql/*
mysqld --initialize-insecure --user=mysql 2>>/dev/null >>/dev/null
mkdir -p /var/run/mysqld
chown -R mysql:mysql /var/lib/mysql /var/run/mysqld
mysqld_safe --user=mysql 2>>/dev/null >>/dev/null &
sleep 20
'''
          }
        }

      }
    }

    stage('Test holland') {
      steps {
        sh '''holland mc --name mysqldump mysqldump
holland mc -f /tmp/mysqldump.conf mysqldump
holland bk mysqldump --dry-run
holland bk mysqldump
holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001 --bkset mysqldump
holland mc --name default mysqldump
holland_cvmysqlsv -bkplevel 1 -attempt 1 -job 123456 -cn 957072-661129 -vm Instance001

# Stopgap measure to check for issue 213
sed -i \'s|^estimate-method = plugin$|estimate-method = const:1K|\' /etc/holland/backupsets/mysqldump.conf
holland bk mysqldump

# test that split command is working as expected
sed -i \'s|^split = no|split = yes|\' /etc/holland/backupsets/mysqldump.conf
holland bk mysqldump
'''
      }
    }

  }
}
