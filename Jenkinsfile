pipeline {
    agent any

    stages {
        stage('Set up Python Environment') {
            steps {
                bat '''
                echo ================================
                echo Setting up Python environment...
                echo ================================

                REM Add Python and Scripts to PATH
                set PATH=%PATH%;C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313\\Scripts

                REM Check Python version
                python --version

                REM Install pip if missing
                python -m ensurepip --upgrade

                REM Upgrade pip
                python -m pip install --upgrade pip

                REM Install dependencies from requirements.txt
                if exist requirements.txt (
                    python -m pip install -r requirements.txt
                ) else (
                    echo "No requirements.txt found, skipping pip install"
                )
                '''
            }
        }

        stage('Run Tests') {
            steps {
                bat '''
                echo ================================
                echo Running Python tests...
                echo ================================
                REM Discover and run all unittest tests
                python -m unittest discover -s tests -p "*.py" || echo "No tests found or tests failed"
                '''
            }
        }

        stage('Deploy') {
            steps {
                bat '''
                echo ================================
                echo Deploying application...
                echo ================================
                REM Add your deployment commands here
                echo "Deploy step placeholder"
                '''
            }
        }
    }

    post {
        always {
            echo "Pipeline finished. Check above logs for details."
        }
        success {
            echo "✅ Pipeline succeeded!"
        }
        failure {
            echo "❌ Pipeline failed!"
        }
    }
}
