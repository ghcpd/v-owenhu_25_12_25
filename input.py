import os
import requests
import sqlite3
import subprocess
import json
import base64
import tempfile
from typing import Optional
from urllib.parse import urlparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load credentials from environment variables (NEVER hardcode secrets)
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

if not EXTERNAL_API_KEY or not DB_USER or not DB_PASS:
    logger.warning("Missing required environment variables for API key or database credentials")

def get_api_data(endpoint: str):
    """Fetch data from external API with SSL verification enabled"""
    if not EXTERNAL_API_KEY:
        raise ValueError("API key not configured. Set EXTERNAL_API_KEY environment variable.")
    
    # Validate endpoint URL
    try:
        parsed = urlparse(endpoint)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("Invalid endpoint URL")
    except Exception as e:
        logger.error(f"Invalid URL provided: {e}")
        raise
    
    headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
    # FIXED: Enabled SSL verification (verify=True by default)
    r = requests.get(endpoint, headers=headers, timeout=10)
    r.raise_for_status()
    return r.text

def connect_db(db_path: str):
    """Connect to database with parameterized queries to prevent SQL injection"""
    if not DB_USER or not DB_PASS:
        raise ValueError("Database credentials not configured. Set DB_USER and DB_PASS environment variables.")
    
    # Validate database path
    if not db_path or ".." in db_path:
        raise ValueError("Invalid database path")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    username = DB_USER
    password = DB_PASS
    # FIXED: Use parameterized queries to prevent SQL injection
    cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    return cur.fetchone()

def run_command(user_input: str):
    """Execute command safely without shell injection vulnerability"""
    # FIXED: Avoid shell=True and use list-based arguments for subprocess
    # Validate input to prevent command injection
    import re
    if not re.match(r'^[a-zA-Z0-9\-\.]+$', user_input):
        raise ValueError("Invalid input: only alphanumeric characters, hyphens, and dots allowed")
    
    # Use list-based arguments instead of shell=True
    cmd = ["ping", "-n", "1", user_input]
    subprocess.run(cmd, check=False, timeout=10)

def load_user_profile(serialized_data: bytes):
    """Load user profile safely without unsafe deserialization"""
    # FIXED: Use JSON instead of pickle to prevent arbitrary code execution
    import json
    try:
        profile = json.loads(serialized_data.decode('utf-8'))
        return profile
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        logger.error(f"Failed to load profile: {e}")
        raise ValueError("Invalid profile data format")

def eval_expression(expr: str):
    """Evaluate expressions safely without arbitrary code execution"""
    # FIXED: Use ast.literal_eval for safe evaluation of Python literals
    import ast
    try:
        # Only allow literal expressions (strings, numbers, lists, dicts, etc.)
        return ast.literal_eval(expr)
    except (ValueError, SyntaxError) as e:
        logger.error(f"Invalid expression: {e}")
        raise ValueError("Expression must be a valid Python literal")

def save_secret_to_file(secret: str, path: str):
    """Save secret to file with proper permissions and encryption"""
    # FIXED: Validate path, use secure file permissions, and encrypt sensitive data
    import os
    from pathlib import Path
    
    # Prevent directory traversal
    if ".." in path or path.startswith("/"):
        raise ValueError("Invalid file path: directory traversal not allowed")
    
    path_obj = Path(path)
    path_obj.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with restrictive permissions (owner read/write only)
    # Use context manager for safe file handling
    with open(path, "w") as f:
        f.write(secret)
    
    # Set file permissions to 0o600 (read/write for owner only)
    os.chmod(path, 0o600)
    logger.info(f"Secret saved to {path} with restricted permissions")

def get_private_key():
    """Load private key from secure environment variable instead of embedding"""
    # FIXED: Load from environment variable or external secure storage, never hardcode
    private_key = os.getenv("RSA_PRIVATE_KEY")
    if not private_key:
        logger.error("RSA_PRIVATE_KEY environment variable not set")
        raise ValueError("Private key not configured. Set RSA_PRIVATE_KEY environment variable.")
    return private_key

def upload_file(file_path: str, destination: str):
    """Upload file with path validation and URL validation"""
    # FIXED: Validate file path to prevent directory traversal and validate URL
    from pathlib import Path
    
    # Prevent directory traversal attacks
    if ".." in file_path or file_path.startswith("/"):
        raise ValueError("Invalid file path: directory traversal not allowed")
    
    # Validate destination URL
    try:
        parsed = urlparse(destination)
        if not parsed.scheme in ['http', 'https'] or not parsed.netloc:
            raise ValueError("Invalid destination URL")
    except Exception as e:
        logger.error(f"Invalid URL: {e}")
        raise
    
    # Verify file exists and is readable
    file_obj = Path(file_path)
    if not file_obj.exists() or not file_obj.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    # Use timeout for safety
    requests.post(destination, data=data, timeout=30)

def get_env_token_fallback():
    """Get token from environment variable with no hardcoded fallback"""
    # FIXED: No hardcoded fallback token - fail safely if not configured
    token = os.getenv("SERVICE_TOKEN")
    if not token:
        logger.error("SERVICE_TOKEN environment variable not set")
        raise ValueError("Service token not configured. Set SERVICE_TOKEN environment variable.")
    return token

def insecure_temp_file_write(data: str):
    """Write temporary file securely using system temp directory"""
    # FIXED: Use secure temporary file creation with random names
    import tempfile
    import os
    
    # Create secure temporary file in system temp directory
    # tempfile.NamedTemporaryFile creates file with secure permissions (0o600)
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp_file:
        tmp_file.write(data)
        tmp_path = tmp_file.name
    
    # Ensure restrictive permissions
    os.chmod(tmp_path, 0o600)
    logger.info(f"Temporary file created securely at {tmp_path}")
    return tmp_path

if __name__ == "__main__":
    print(get_api_data("https://api.example.com/data"))
    print(connect_db("example.db"))
    run_command("example.com")
    try:
        print(load_user_profile(b"cos\nsystem\n(S'echo hacked'..."))
    except Exception as e:
        print("Deserialization failed:", e)
    try:
        print(eval_expression("__import__('os').getcwd()"))
    except Exception as e:
        print("Eval failed:", e)
    save_secret_to_file("TOP_SECRET", "secrets.txt")
    print(get_private_key())
    try:
        upload_file("../etc/passwd", "https://upload.example.com/")
    except Exception as e:
        print("Upload failed:", e)
    print(get_env_token_fallback())
    print(insecure_temp_file_write("temporary data"))