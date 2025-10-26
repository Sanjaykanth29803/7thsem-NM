pipeline {
    agent any

    stages {
        stage('Set up Python Environment') {
            steps {
                bat '''
                echo Setting up Python environment...
                python --version
                python -m pip install --upgrade pip
                python -m pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat '''
                echo Running tests...
                # add your test commands here, e.g.
                python -m unittest discover
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                echo Deploying app...
                # add your deployment commands here
                '''
            }
        }
    }
}
