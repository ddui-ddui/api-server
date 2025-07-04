#!/bin/bash
echo "Production deploy starting..."

# 기존 컨테이너 종료
docker-compose -f docker-compose.prod.yml down

# 새 버전 배포
docker-compose -f docker-compose.prod.yml up --build -d

echo "Production deploy complete!"