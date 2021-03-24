pipeline {
  agent {
    docker {
      image 'python'
    }

  }
  stages {
    stage('build') {
      steps {
        sh '''pip install pylint
pylint holland

pylint_failed=0
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