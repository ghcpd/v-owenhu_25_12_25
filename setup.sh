#!/usr/bin/env bash
set -euo pipefail
python -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Environment prepared. To run tests:"
echo "  . .venv/bin/activate && python auto_test.py"
