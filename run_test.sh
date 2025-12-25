#!/bin/bash

# run_test.sh - Test script for Linux/macOS

set -e

echo "================================================"
echo "Running security audit tests (Linux/macOS)"
echo "================================================"
echo ""

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG_FILE="${SCRIPT_DIR}/logs/test_run.log"

# Create logs directory if it doesn't exist
mkdir -p "${SCRIPT_DIR}/logs"

# Timestamp function
log_timestamp() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')]"
}

# Write to both console and log file
log() {
    echo "$1" | tee -a "$LOG_FILE"
}

# Start logging
{
    log "$(log_timestamp) TEST EXECUTION STARTED"
    log "================================================"
    
    # Load environment variables
    if [ -f .env ]; then
        log "$(log_timestamp) Loading environment variables from .env"
        set -a
        source .env
        set +a
    else
        log "$(log_timestamp) WARNING: .env file not found. Using default/empty environment variables."
    fi
    
    # Test input_backup.py (original vulnerable version)
    log ""
    log "$(log_timestamp) --- Testing input_backup.py (Original Vulnerable Version) ---"
    if python3 input_backup.py 2>&1 | tee -a "$LOG_FILE"; then
        log "$(log_timestamp) input_backup.py executed (may contain expected errors)"
    else
        log "$(log_timestamp) input_backup.py execution completed with some errors (expected)"
    fi
    
    log ""
    log "$(log_timestamp) --- Testing input.py (Secured Version) ---"
    # Test input.py (secured version)
    if python3 input.py 2>&1 | tee -a "$LOG_FILE"; then
        log "$(log_timestamp) input.py executed successfully"
        TEST_STATUS="TEST PASSED"
    else
        log "$(log_timestamp) input.py execution completed with some errors"
        TEST_STATUS="TEST FAILED"
    fi
    
    log ""
    log "================================================"
    log "$(log_timestamp) $TEST_STATUS"
    log "$(log_timestamp) TEST EXECUTION COMPLETED"
} >> "$LOG_FILE" 2>&1

# Print final status
echo ""
echo "================================================"
tail -n 5 "$LOG_FILE"
echo "================================================"
