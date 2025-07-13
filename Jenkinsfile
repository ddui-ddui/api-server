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
            steps {
                echo '🚀 Deploying to staging...'
                sh 'chmod +x scripts/deploy-staging.sh'

                script {
                    try {
                        sh './scripts/deploy-staging.sh'
                        env.DEPLOYMENT_STATUS = 'SUCCESS'
                    } catch (Exception e) {
                        echo "❌ Deployment failed: ${e.getMessage()}"
                        env.DEPLOYMENT_STATUS = 'FAILED'
                        throw e
                    }
                }
            }
        }

        stage('Rollback on Failure') {
            when {
                environment name: 'DEPLOYMENT_STATUS', value: 'FAILED'
            }
            steps {
                echo '🔄 Starting rollback...'
                sh 'chmod +x scripts/roll-back.sh'
                sh './scripts/roll-back.sh'
            }
        }
    }
    
    post {
        failure {
            echo '❌ Pipeline failed!'
            script {
                if (env.DEPLOYMENT_STATUS == 'FAILED') {
                    echo '🔄 Rollback was attempted'
                }
            }
        }
        success {
            echo '✅ Pipeline succeeded!'
        }
    }
}