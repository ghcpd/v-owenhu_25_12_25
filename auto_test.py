import os
import platform
import subprocess
import datetime
import shutil

def detect_environment():
    system = platform.system()
    if system == 'Windows':
        return 'windows'
    else:
        # Assume Linux/macOS/Docker
        return 'linux'

def run_test(file_name):
    env = detect_environment()
    timestamp = datetime.datetime.now().isoformat()
    
    with open('logs/test_run.log', 'a') as log:
        log.write(f"{timestamp} - Running test for {file_name}\n")
    
    if env == 'windows':
        script = 'run_test.bat'
    else:
        script = './run_test.sh'
    
    # Backup current input.py if testing backup
    original_name = 'input.py'
    backup_name = 'input_temp.py'
    if file_name != original_name:
        shutil.move(original_name, backup_name)
        shutil.copy(file_name, original_name)
    
    try:
        result = subprocess.run([script], capture_output=True, text=True, shell=(env=='windows'))
        output = result.stdout + result.stderr
        status = "TEST PASSED" if result.returncode == 0 else "TEST FAILED"
        
        with open('logs/test_run.log', 'a') as log:
            log.write(f"{timestamp} - File: {file_name}\n")
            log.write(f"Output: {output}\n")
            log.write(f"Status: {status}\n\n")
    finally:
        # Restore if backed up
        if file_name != original_name:
            shutil.move(backup_name, original_name)

def main():
    # Clear log
    with open('logs/test_run.log', 'w') as log:
        log.write("Test Run Log\n\n")
    
    run_test('input_backup.py')
    run_test('input.py')

if __name__ == "__main__":
    main()