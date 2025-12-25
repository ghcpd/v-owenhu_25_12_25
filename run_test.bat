@echo off
setlocal enabledelayedexpansion
if "%1"=="" (
  set FILES=input_backup.py input.py
) else (
  set FILES=%1
)
if not exist logs mkdir logs
for %%F in (%FILES%) do (
  echo -------------------- >> logs\test_run.log
  echo %DATE% %TIME% - START - %%F >> logs\test_run.log
  set SAFE_TEST=1
  set PYTHONPATH=tests
  python %%F > logs\%%F.out 2>&1
  if errorlevel 1 (
    type logs\%%F.out >> logs\test_run.log
    echo %DATE% %TIME% - %%F - TEST FAILED (exit %ERRORLEVEL%) >> logs\test_run.log
  )
  if not errorlevel 1 (
    type logs\%%F.out >> logs\test_run.log
    echo %DATE% %TIME% - %%F - TEST PASSED >> logs\test_run.log
  )
)
endlocal
