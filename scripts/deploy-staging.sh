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

echo "Staging deploy complete!"