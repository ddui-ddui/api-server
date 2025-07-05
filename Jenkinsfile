pipeline {
    agent any
    
    stages {
        // stage('Checkout') {
        //     steps {
        //         echo '📥 Checking out code...'
        //         // Git checkout은 자동으로 수행됨
        //     }
        // }
        
        stage('Test') {
            steps {
                echo '🧪 Running tests...'
                sh 'chmod +x scripts/test.sh'
                sh './scripts/test.sh'
            }
        }
        
        stage('Deploy to Staging') {
            when {
                branch 'staging'
            }
            steps {
                echo '🚀 Deploying to staging...'
                sh 'chmod +x scripts/deploy-staging.sh'
                sh './scripts/deploy-staging.sh'
            }
        }
    }
    
    post {
        failure {
            echo '❌ Pipeline failed!'
        }
        success {
            echo '✅ Pipeline succeeded!'
        }
    }
}