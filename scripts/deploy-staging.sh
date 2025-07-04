#!/bin/bash
echo "Staging deploy starting..."

# 기존 컨테이너 종료
docker-compose -f docker-compose.staging.yml down

# 새 버전 배포
docker-compose -f docker-compose.staging.yml up --build -d

echo "Staging deploy complete!"