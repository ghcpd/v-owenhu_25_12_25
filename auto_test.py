#!/usr/bin/env python3
import os
import platform
import subprocess
from datetime import datetime

LOG_PATH = os.path.join('logs', 'test_run.log')
os.makedirs('logs', exist_ok=True)

def ts():
    return datetime.utcnow().isoformat() + 'Z'

def run_script(script, target=None):
    if platform.system().lower().startswith('win'):
        cmd = ['cmd', '/c', script]
        if target:
            cmd.append(target)
    else:
        cmd = ['bash', script]
        if target:
            cmd.append(target)
    env = os.environ.copy()
    env['SAFE_TEST'] = '1'
    env['PYTHONPATH'] = (env.get('PYTHONPATH', '') + os.pathsep + 'tests').lstrip(os.pathsep)
    proc = subprocess.run(cmd, capture_output=True, text=True, env=env)
    return proc.returncode, proc.stdout + proc.stderr

# Static source checks to detect common insecure patterns
# Checks are more precise to reduce false positives; some checks are allowed if gated (e.g., ALLOW_PICKLE)
CHECKS = [
    {'pattern': r"EXTERNAL_API_KEY\s*=\s*['\"]", 'desc': "Hardcoded API key", 'allow_if': None},
    {'pattern': r"DB_USER\s*=\s*['\"]|DB_PASS\s*=\s*['\"]", 'desc': "Hardcoded DB credentials", 'allow_if': None},
    {'pattern': r"-----BEGIN RSA PRIVATE KEY-----", 'desc': "Hardcoded private key", 'allow_if': None},
    {'pattern': r"\beval\(", 'desc': "Use of eval()", 'allow_if': None},
    {'pattern': r"pickle\.loads\(", 'desc': "Use of pickle.loads()", 'allow_if': 'ALLOW_PICKLE'},
    {'pattern': r"verify\s*=\s*False", 'desc': "Disabled SSL verification (verify=False)", 'allow_if': None},
    {'pattern': r"shell\s*=\s*True", 'desc': "subprocess with shell=True", 'allow_if': None},
    {'pattern': r"DEFAULT_TOKEN_IN_CODE", 'desc': "Default token in source", 'allow_if': None},
    {'pattern': r"/tmp/vuln_temp\.txt", 'desc': "Predictable temporary file path", 'allow_if': None},
    # Detect SQL injection only when using f-strings, .format() or % formatting for SQL
    {'pattern': r"(f[\'\"]SELECT.*\{)|(\.format\()|(%\s*\()", 'desc': "Potential SQL injection via f-string/.format/%", 'allow_if': None},
]

import re as _re

def analyze_source(path):
    issues = []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            full = ''.join(lines)
    except Exception as e:
        return [("file_read_error", str(e))]
    for idx, raw_line in enumerate(lines, start=1):
        # Remove simple inline comments to avoid matching commented guidance
        code_line = raw_line.split('#', 1)[0]
        for check in CHECKS:
            pattern = check['pattern']
            desc = check['desc']
            allow_if = check['allow_if']
            if allow_if and allow_if in full:
                # This check is gated in-source (e.g., ALLOW_PICKLE), skip
                continue
            if _re.search(pattern, code_line):
                issues.append((desc, idx, raw_line.strip()))
    return issues

def output_has_errors(output):
    # Look for tracebacks, unhandled Exceptions, or common error messages
    lowered = output.lower()
    if 'traceback' in lowered or 'exception' in lowered or 'error' in lowered:
        return True
    return False


def log_entry(fn, rc, output):
    issues = analyze_source(fn)
    problematic = False
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write('------------------------------------------------------------\n')
        f.write(f"{ts()} - START - {fn}\n")
        f.write(output + '\n')
        if issues:
            problematic = True
            f.write(f"{ts()} - {fn} - SOURCE ISSUES FOUND:\n")
            for desc, ln, snippet in issues:
                f.write(f"  - {desc} (line {ln}): {snippet}\n")
        # Also fail on runtime error output even if exit code is 0
        if output_has_errors(output):
            problematic = True
            f.write(f"{ts()} - {fn} - RUNTIME ERRORS DETECTED IN OUTPUT\n")
        if rc != 0 or problematic:
            f.write(f"{ts()} - {fn} - TEST FAILED (exit {rc})\n")
        else:
            f.write(f"{ts()} - {fn} - TEST PASSED\n")
    # Return final pass/fail as boolean
    return not (rc != 0 or problematic)


def main():
    system = platform.system().lower()
    if system.startswith('win'):
        script = 'run_test.bat'
    else:
        script = 'run_test.sh'
    # Run tests for backup and patched file in sequence
    targets = ['input_backup.py', 'input.py']
    overall_success = True
    for t in targets:
        rc, out = run_script(script, t)
        passed = log_entry(t, rc, out)
        if not passed:
            overall_success = False
    # Final summary
    with open(LOG_PATH, 'a', encoding='utf-8') as f:
        f.write('============================================================\n')
        f.write(f"{ts()} - AUTO_TEST SUMMARY - {'ALL PASSED' if overall_success else 'SOME FAILED'}\n")
    return 0 if overall_success else 1

if __name__ == '__main__':
    rc = main()
    exit(rc)
