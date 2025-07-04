#!/bin/bash
echo "🧪 Running tests..."

pytest app/tests/ -v --tb=short --cov=app

if [ $? -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Tests failed!"
    exit 1
fi