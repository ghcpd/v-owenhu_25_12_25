#!/bin/bash

# Run test script for Linux/macOS

# Set environment variables for testing
export EXTERNAL_API_KEY="test_key"
export DB_USER="test_user"
export DB_PASS="test_pass"
export SERVICE_TOKEN="test_token"

# Run the script and capture output
python3 input.py > output.txt 2>&1

# Filter out traceback lines
grep -v "File " output.txt > filtered.txt

# Check for sensitive data leakage in filtered output
if grep -q "MIICWwIBAAKBgQC7" filtered.txt; then
    echo "TEST FAILED"
    exit 1
fi

cwd=$(pwd)
if grep -q "$cwd" filtered.txt; then
    echo "TEST FAILED"
    exit 1
fi

echo "TEST PASSED"
exit 0