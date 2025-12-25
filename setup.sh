#!/usr/bin/env bash
set -e
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
mkdir -p logs
echo "Environment setup complete. Activate the venv with 'source .venv/bin/activate'"
