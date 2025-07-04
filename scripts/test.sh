#!/bin/bash
echo "Running tests..."

# 라이브러리 설치
echo "Installing dependencies..."
pip3.11 install --upgrade pip
pip3.11 install -r app/requirements.txt

# 테스트
echo "Running tests..."
pytest app/tests/ -v --tb=short
# --cov=app
# 코드 커버리지 사용할 시 추가하면 되는데 실행 환경에 모두 pytest-cov를 설치해야함.

if [ $? -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Tests failed!"
    exit 1
fi