#!/bin/bash
echo "Staging deploy starting..."

# 기존 컨테이너 종료
if ! docker-compose -f docker-compose.staging.yml down; then
    echo "Failed to stop containers"
    exit 1
fi

# 새 버전 배포
if ! docker-compose -f docker-compose.staging.yml up --build -d; then
    echo "Failed to deploy"
    exit 1
fi

echo "Waiting for services to start..."
sleep 15

# 서비스 상태 확인
echo "Checking container status..."
if ! docker-compose -f docker-compose.staging.yml ps | grep -q "Up"; then
    echo "Services are not running properly"
    echo "Container logs:"
    docker-compose -f docker-compose.staging.yml logs --tail=50
    exit 1
fi

# 헬스체크 엔드포인트 확인
echo "Performing health check..."
HEALTH_CHECK_URL="http://211.206.133.190:4500/api/v1/commons/health"
MAX_ATTEMPTS=15
ATTEMPT=1

while [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
    echo "Health check attempt $ATTEMPT/$MAX_ATTEMPTS..."
    
    if curl -f -s "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "Health check passed!"
        echo "Staging deploy complete!"
        exit 0
    fi
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo "Health check failed after $MAX_ATTEMPTS attempts"
        echo "Service logs:"
        docker-compose -f docker-compose.staging.yml logs --tail=100
        echo "Container status:"
        docker-compose -f docker-compose.staging.yml ps
        exit 1
    fi
    
    echo "Waiting for service to be ready..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
done