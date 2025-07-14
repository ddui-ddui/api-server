pipeline {
    agent any
    
    stages {
        stage('Test') {
            steps {
                echo '🧪 Running tests...'
                sh 'chmod +x scripts/test.sh'
                sh './scripts/test.sh'
            }
        }
        
        stage('Deploy to prod') {
            steps {
                echo 'Deploying to prod...'
                sh 'chmod +x scripts/deploy-prod.sh'

                script {
                    try {
                        sh './scripts/deploy-prod.sh'
                        env.DEPLOYMENT_STATUS = 'SUCCESS'
                    } catch (Exception e) {
                        echo "Deployment failed: ${e.getMessage()}"
                        env.DEPLOYMENT_STATUS = 'FAILED'
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
            post {
                unstable {
                    echo 'Starting rollback due to deployment failure...'
                    sh 'chmod +x scripts/roll-back.sh'
                    sh './scripts/roll-back.sh'
                }
            }
        }
    }
    
    post {
        unstable {
            echo 'Pipeline unstable - rollback completed'
        }
        success {
            echo 'Pipeline succeeded!'
        }
    }
}