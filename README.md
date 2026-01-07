# Security Hardening & Test Harness

## Overview ✅
This workspace contains an audited and secured version of `input.py`, a backup of the original file (`input_backup.py`), a vulnerability report (`report.json`), environment replication files, test scripts, and an automated test runner.

Files generated:

- `input_backup.py` — exact copy of the original, unmodified source (for comparison).
- `input.py` — **secure** version with fixes applied (parameterized SQL, safe deserialization, no eval, secure subprocess usage, secrets from env, safe file operations, request timeouts/verify, etc.).
- `report.json` — structured vulnerability report with line numbers and explanations.
- `requirements.txt` — Python dependencies.
- `Dockerfile` — container image to run `auto_test.py`.
- `setup.sh` — convenience script to create a virtual environment and install dependencies.
- `run_test.sh` / `run_test.bat` — platform-specific test scripts to run one or both target files; they set `SAFE_TEST=1` to prevent destructive operations during testing.
- `auto_test.py` — automatic test runner that detects environment, runs tests for `input_backup.py` and `input.py` in sequence, and appends results to `logs/test_run.log`.
- `tests/sitecustomize.py` — test harness that stubs dangerous operations (network calls, subprocesses, pickle) when `SAFE_TEST=1` is set.
- `logs/test_run.log` — generated during tests; contains timestamped output and final status lines.

## Setup 🔧
Linux/macOS:
1. Run `./setup.sh` to create a virtual environment and install dependencies.
2. Activate the virtualenv: `source .venv/bin/activate`

Windows (PowerShell):
1. `python -m venv .venv`
2. `.\.venv\Scripts\Activate.ps1`
3. `pip install -r requirements.txt`

## Running Tests ▶️
Linux/macOS:
- Run all tests: `./run_test.sh`
- Run single test: `./run_test.sh input.py` or `./run_test.sh input_backup.py`

Windows:
- Run all tests: `run_test.bat`
- Run single test: `run_test.bat input.py` or `run_test.bat input_backup.py`

Both scripts run tests with `SAFE_TEST=1` and add `tests/` to `PYTHONPATH` so the harness can stub dangerous operations.

## Automatic Test Runner (recommended) ⚙️
- Execute `python auto_test.py`. This will detect your platform and run the appropriate test script for `input_backup.py` and `input.py` in sequence, appending timestamped logs to `logs/test_run.log` and ending each test block with `TEST PASSED` or `TEST FAILED`.

## Interpreting logs 📝
- Logs are stored in `logs/test_run.log`.
- Each test block begins with an ISO8601 timestamp and ends with a status line: `TEST PASSED` or `TEST FAILED (exit <code>)`.

## Notes & Security Recommendations 💡
- **Secrets must** be stored in environment variables or a secret manager. Do NOT hardcode secrets.
- Consider using a secure secret storage (HashiCorp Vault, Azure Key Vault, AWS Secrets Manager, etc.).
- For production, remove or restrict any debug or `SAFE_TEST`-style flags.

If you'd like, I can run `auto_test.py` locally in this workspace to produce initial logs and demonstrate the test results. ✅
