#!/bin/bash
echo "Starting rollback process..."

# 현재 커밋 정보 저장
FAILED_COMMIT=$(git rev-parse HEAD)
echo "Failed commit: $FAILED_COMMIT"

# 이전 커밋으로 롤백
echo "Rolling back to previous commit..."
if ! git reset --hard HEAD~1; then
    echo "Failed to rollback git commit"
    exit 1
fi

ROLLBACK_COMMIT=$(git rev-parse HEAD)
echo "Rolled back to commit: $ROLLBACK_COMMIT"

# 기존 컨테이너 종료
echo "Stopping current containers..."
docker-compose -f docker-compose.staging.yml down || echo "⚠️ Container stop failed, continuing..."

# 이전 버전으로 재배포
echo "Deploying previous version..."
if ! docker-compose -f docker-compose.staging.yml up --build -d; then
    echo "Critical: Failed to deploy rollback version"
    echo "System is in unstable state"
    exit 1
fi

echo "Waiting for rollback services to start..."
sleep 15

# 롤백 헬스체크
echo "Performing rollback health check..."
HEALTH_CHECK_URL="http://211.206.133.190:4500/api/v1/health"
MAX_ATTEMPTS=10
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Rollback health check attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "Rollback successful!"
        echo "Service restored to commit: $ROLLBACK_COMMIT"
        exit 0
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "Rollback health check failed"
        echo "Service logs:"
        docker-compose -f docker-compose.staging.yml logs --tail=50
        # Git 상태 복원 시도
        git reset --hard $CURRENT_COMMIT
        exit 1
    fi
    
    echo "Waiting for rollback service to be ready..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done