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
                set PATH=C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313\\Scripts;%PATH%
                
                REM Check Python version
                python --version

                REM Ensure pip is installed
                python -m ensurepip --upgrade

                REM Upgrade pip
                python -m pip install --upgrade pip

                REM Install dependencies if requirements.txt exists
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
                
                REM Run tests only if the 'tests' folder exists
                if exist tests (
                    python -m unittest discover -s tests -p "*.py"
                ) else (
                    echo "No tests folder found, skipping tests"
                )
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
                '''
            }
        }
    }

    post {
        success {
            echo "✅ Pipeline completed successfully!"
        }
        failure {
            echo "❌ Pipeline failed! Check logs above for details."
        }
    }
}
