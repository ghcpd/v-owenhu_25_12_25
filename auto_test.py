#!/usr/bin/env python3
"""Automatic test runner that detects environment and runs the platform
appropriate test wrapper for both the backup (vulnerable) and the
fixed file, logging results to logs/test_run.log.
"""
from __future__ import annotations

import datetime
import os
import platform
import shlex
import shutil
import subprocess
import sys
from typing import List

LOG_PATH = os.path.join("logs", "test_run.log")
ROOT = os.path.dirname(__file__)


def _now() -> str:
    return datetime.datetime.utcnow().isoformat() + "Z"


def detect_runner() -> str:
    system = platform.system().lower()
    # prefer the shell wrappers if available
    if system == "windows":
        return os.path.join(ROOT, "run_test.bat")
    # linux / darwin
    return os.path.join(ROOT, "run_test.sh")


def run_command(cmd: List[str], env=None, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, text=True, timeout=timeout)


def ensure_logs_dir():
    d = os.path.dirname(LOG_PATH)
    os.makedirs(d, exist_ok=True)


def write_log(lines: str):
    ensure_logs_dir()
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(lines)


def run_test_py_for_file(target_file: str) -> int:
    cmd = [sys.executable, os.path.join(ROOT, "run_tests.py"), target_file]
    try:
        proc = run_command(cmd, timeout=60)
    except Exception as exc:
        write_log(f"{_now()} {target_file} - ERROR running runner: {exc}\n")
        return 3

    write_log(f"{_now()} {target_file} - exit={proc.returncode}\n")
    write_log(proc.stdout + "\n")
    write_log(f"{_now()} {target_file} - {'TEST PASSED' if proc.returncode==0 else 'TEST FAILED'}\n")
    return proc.returncode


def run_wrapper(runner: str) -> int:
    # run the platform wrapper (this performs the combined expectation check)
    if runner.endswith('.sh'):
        cmd = ["/bin/bash", runner]
    else:
        cmd = [runner]
    try:
        proc = run_command(cmd, timeout=120)
    except Exception as exc:
        write_log(f"{_now()} wrapper - ERROR running wrapper: {exc}\n")
        return 3

    write_log(f"{_now()} wrapper - exit={proc.returncode}\n")
    write_log(proc.stdout + "\n")
    write_log(f"{_now()} wrapper - {'TEST PASSED' if proc.returncode==0 else 'TEST FAILED'}\n")
    return proc.returncode


def main() -> int:
    runner = detect_runner()

    results = {}
    for target in ["input_backup.py", "input.py"]:
        rc = run_test_py_for_file(target)
        results[target] = rc

    # also run the platform wrapper (authoritative combined check)
    wrapper_rc = run_wrapper(runner)
    write_log(f"{_now()} OVERALL: {'TEST PASSED' if wrapper_rc==0 else 'TEST FAILED'}\n")
    return 0 if wrapper_rc == 0 else 2


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
