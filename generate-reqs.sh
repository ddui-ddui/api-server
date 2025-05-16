#!/bin/bash

echo "📦 Generating requirements.txt with pipreqs..."
pipreqs ./src --force --encoding=utf-8 --savepath=requirements.txt

echo "🔍 Ensuring pipreqs is in dev-requirements.txt..."
if ! grep -q "^pipreqs" dev-requirements.txt; then
    echo "pipreqs" >> dev-requirements.txt
    echo "✔ pipreqs added to dev-requirements.txt"
else
    echo "✔ pipreqs already present in dev-requirements.txt"
fi