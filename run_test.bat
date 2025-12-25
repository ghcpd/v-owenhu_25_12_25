@echo off

REM Run test script for Windows

REM Set environment variables for testing
set EXTERNAL_API_KEY=test_key
set DB_USER=test_user
set DB_PASS=test_pass
set SERVICE_TOKEN=test_token

REM Run the script and capture output
python input.py > output.txt 2>&1

REM Filter out traceback lines
findstr /v "File " output.txt > filtered.txt

REM Check for sensitive data leakage in filtered output
findstr /c:"MIICWwIBAAKBgQC7" filtered.txt >nul
if %errorlevel% equ 0 (
    echo TEST FAILED
    exit /b 1
)

for /f %%i in ('cd') do set cwd=%%i
findstr "%cwd%" filtered.txt >nul
if %errorlevel% equ 0 (
    echo TEST FAILED
    exit /b 1
)

echo TEST PASSED
exit /b 0