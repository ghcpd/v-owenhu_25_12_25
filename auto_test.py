import os
import platform
import subprocess
import sys
from datetime import datetime

LOG_DIR = os.path.join(os.path.dirname(__file__), "logs")
LOG_FILE = os.path.join(LOG_DIR, "test_run.log")

os.makedirs(LOG_DIR, exist_ok=True)


def timestamp():
    return datetime.utcnow().isoformat() + "Z"


def run_script_for_module(script: str, module_path: str):
    if os.name == "nt":
        # run the Python test runner directly to avoid batch/quoting issues
        cmd = [sys.executable, "-u", "tests/runner.py", module_path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return proc.returncode, proc.stdout
    else:
        cmd = [script, module_path]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        return proc.returncode, proc.stdout


def detect_platform_script():
    if os.name == "nt":
        return os.path.join(os.getcwd(), "run_test.bat")
    # detect docker
    if os.path.exists("/.dockerenv"):
        return os.path.join(os.getcwd(), "run_test.sh")
    return os.path.join(os.getcwd(), "run_test.sh")


def log_and_print(msg: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")
    print(msg)


def main():
    script = detect_platform_script()
    modules = ["input_backup.py", "input.py"]
    results = {}

    for m in modules:
        path = os.path.join(os.getcwd(), m)
        log_and_print(f"[{timestamp()}] Running tests for {m}")
        rc, out = run_script_for_module(script, path)
        log_and_print(f"[{timestamp()}] OUTPUT for {m}:\n{out}")
        status = "TEST PASSED" if rc == 0 else "TEST FAILED"
        log_and_print(f"[{timestamp()}] {m} final status: {status}")
        results[m] = rc

    # Determine overall success: fixed input.py must pass (rc==0) and backup must fail (rc!=0)
    backup_ok = results.get("input_backup.py", 1) != 0
    fixed_ok = results.get("input.py", 1) == 0
    final = "TEST PASSED" if (backup_ok and fixed_ok) else "TEST FAILED"
    log_and_print(f"[{timestamp()}] OVERALL: {final}")
    sys.exit(0 if final == "TEST PASSED" else 2)


if __name__ == "__main__":
    main()