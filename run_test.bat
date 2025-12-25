@echo off
REM run_test.bat - Test script for Windows

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ================================================
echo Running security audit tests (Windows)
echo ================================================
echo.

set LOG_FILE=%CD%\logs\test_run.log
if not exist logs mkdir logs

REM Timestamp helper
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c-%%a-%%b)
for /f "tokens=1-2 delims=/:" %%a in ('time /t') do (set mytime=%%a:%%b)

REM Start logging
(
    echo [%mydate% %mytime%] TEST EXECUTION STARTED
    echo ================================================
    
    REM Load environment variables from .env if it exists
    if exist .env (
        echo [%mydate% %mytime%] Loading environment variables from .env
        for /f "usebackq delims==" %%a in (.env) do (
            if not "%%a"=="" (
                set "%%a"
            )
        )
    ) else (
        echo [%mydate% %mytime%] WARNING: .env file not found. Using default/empty environment variables.
    )
    
    REM Test input_backup.py
    echo.
    echo [%mydate% %mytime%] --- Testing input_backup.py ^(Original Vulnerable Version^) ---
    python input_backup.py
    if !errorlevel! equ 0 (
        echo [%mydate% %mytime%] input_backup.py executed ^(may contain expected errors^)
    ) else (
        echo [%mydate% %mytime%] input_backup.py execution completed with errors ^(expected^)
    )
    
    echo.
    echo [%mydate% %mytime%] --- Testing input.py ^(Secured Version^) ---
    REM Test input.py
    python input.py
    if !errorlevel! equ 0 (
        echo [%mydate% %mytime%] input.py executed successfully
        set TEST_STATUS=TEST PASSED
    ) else (
        echo [%mydate% %mytime%] input.py execution completed with some errors
        set TEST_STATUS=TEST FAILED
    )
    
    echo.
    echo ================================================
    echo [%mydate% %mytime%] !TEST_STATUS!
    echo [%mydate% %mytime%] TEST EXECUTION COMPLETED
) >> "%LOG_FILE%"

REM Print final status
echo.
echo ================================================
type "%LOG_FILE%" | findstr /r "^\[.*\]" | tail -5
echo ================================================
pause
