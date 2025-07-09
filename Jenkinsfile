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
        
        stage('Deploy to Production') {
            // when {
            //     branch 'main'
            // }
            steps {
                echo '🚀 Deploying to prod...'
                sh 'chmod +x scripts/deploy-prod.sh'
                sh './scripts/deploy-prod.sh'
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