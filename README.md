# Security audit and fixes for `input.py`

## Overview

This workspace contains:

- `input.py` — **secured** version (no hardcoded secrets, safe deserialization/eval, parameterized SQL, safe subprocess usage).
- `input_backup.py` — original vulnerable file (kept as a backup for auditing).
- `tests/runner.py` — test runner used by `run_test.*` to validate security fixes.
- `run_test.sh` / `run_test.bat` — platform test wrappers.
- `auto_test.py` — automatic test executor that runs tests for both `input_backup.py` and `input.py` and writes `logs/test_run.log`.
- `report.json` — structured vulnerability report with fixes applied.
- `Dockerfile`, `requirements.txt`, `setup.sh` — environment replication files.


## Setup

Linux / macOS

1. Create a virtualenv and install dependencies:
   - ./setup.sh
2. Export required environment variables for testing (example):
   - export EXTERNAL_API_KEY=example_key
   - export DB_USER=admin
   - export DB_PASS=example
   - export SECRET_ENC_KEY=mysecret
   - export SERVICE_TOKEN=token_value

Windows

1. Create a venv and install requirements:
   - python -m venv .venv
   - .\.venv\Scripts\activate
   - pip install -r requirements.txt
2. Set the environment variables in PowerShell or cmd.

Docker

1. docker build -t secure-input .
2. docker run --rm secure-input


## Running tests

- Linux/macOS: ./run_test.sh input.py
- Windows: run_test.bat input.py
- Automatic (runs both backup and fixed): python auto_test.py

Logs are appended to `logs/test_run.log` with timestamps and final status lines.


## Interpreting results

- `TEST PASSED` (overall in `auto_test.py`) means:
  - `input_backup.py` shows the original vulnerabilities (expected to fail checks), and
  - `input.py` passes the security checks (fixed).

- `TEST FAILED` indicates one or more checks did not meet the expectations.


## Notes

- Secrets are loaded from environment variables; do **not** hardcode secrets into source control.
- `save_secret_to_file` requires `SECRET_ENC_KEY` to be set; otherwise it refuses to store secrets on disk.
- `load_user_profile` only accepts JSON payloads — pickle is explicitly rejected.
