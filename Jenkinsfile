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
