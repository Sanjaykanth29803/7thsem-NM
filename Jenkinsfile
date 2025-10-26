stage('Set up Python Environment') {
    steps {
        bat '''
        echo Setting up Python environment...
        set PATH=%PATH%;C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313;C:\\Users\\kaviy\\AppData\\Local\\Programs\\Python\\Python313\\Scripts
        python --version
        python -m ensurepip --upgrade
        python -m pip install --upgrade pip
        python -m pip install -r requirements.txt
        '''
    }
}
