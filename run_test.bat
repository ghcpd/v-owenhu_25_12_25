@echo off
if "%1"=="" (
  echo Usage: run_test.bat path\to\module
  exit /b 2
)
set MODULE=%1
python -u tests\runner.py "%MODULE%"