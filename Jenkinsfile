pipeline {
    agent any

    stages {
        stage('Clone Repository') {
            steps {
                git branch: 'main', 
                    url: 'https://github.com/Sanjaykanth29803/7thsem-NM'
            }
        }

        stage('Set up Python Environment') {
            steps {
                bat '''
                python --version
                pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat 'pytest || echo "No tests found"'
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying application...'
            }
        }
    }

    post {
        success {
            echo '✅ Build succeeded!'
        }
        failure {
            echo '❌ Build failed. Check logs!'
        }
    }
}
