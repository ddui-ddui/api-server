@echo off
echo 📦 Generating requirements.txt with pipreqs...
pipreqs src --force --encoding=utf-8 --savepath=requirements.txt

findstr /B /C:"pipreqs" dev-requirements.txt > nul
if %ERRORLEVEL% NEQ 0 (
    echo pipreqs >> dev-requirements.txt
    echo ✔ pipreqs added to dev-requirements.txt
) else (
    echo ✔ pipreqs already present in dev-requirements.txt
)