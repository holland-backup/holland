pipeline {
  agent {
    docker {
      image 'soulen3/holland:centos7_mariadb_10.5'
    }

  }
  stages {
    stage('build') {
      steps {
        sh 'sudo /entrypoint.sh'
      }
    }

  }
  environment {
    FORK = 'https://github.com/holland-backup/holland.git'
    DEBUG = 'True'
    BRANCH = 'env.BRANCH_NAME'
  }
}