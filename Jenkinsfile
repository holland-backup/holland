pipeline {
  agent {
    docker {
      image 'ubuntu'
      args '-u root:root'
    }

  }
  stages {
    stage('Install pylint') {
      steps {
        sh '''apt-get update
apt-get install -y python3-pip
pip3 install pylint
'''
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

        stage('pylint plugins') {
          steps {
            sh '''pylint_failed=0
for d in $(ls -d ./plugins/*/holland ./contrib/holland-commvault/holland_commvault)
do
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

      }
    }

  }
}