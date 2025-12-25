@echo off
rem Wrapper for Windows: expect input_backup.py to be vulnerable and input.py to be clean
set PY=python
%PY% run_tests.py input_backup.py
set BACKUP_EXIT=%ERRORLEVEL%
%PY% run_tests.py input.py
set FIXED_EXIT=%ERRORLEVEL%
echo input_backup.py exit: %BACKUP_EXIT% (expected non-zero)
echo input.py exit: %FIXED_EXIT% (expected 0)
if %BACKUP_EXIT% NEQ 0 if %FIXED_EXIT% EQU 0 (
  echo TESTS OK: backup shows vulnerabilities and fixed file is clean
  exit /b 0
) else (
  echo TESTS FAILED: expectations not met
  exit /b 2
)

rem Wrapper for Windows: expect input_backup.py to be vulnerable and input.py to be clean
set PY=python













)  exit /b 2  echo TESTS FAILED: expectations not met) else (  exit /b 0  echo TESTS OK: backup shows vulnerabilities and fixed file is cleanif %BACKUP_EXIT% NEQ 0 if %FIXED_EXIT% EQU 0 (echo input.py exit: %FIXED_EXIT% (expected 0)echo input_backup.py exit: %BACKUP_EXIT% (expected non-zero)set FIXED_EXIT=%ERRORLEVEL%%PY% run_tests.py input.pyset BACKUP_EXIT=%ERRORLEVEL%n%PY% run_tests.py input_backup.py