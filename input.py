import os
import requests
import sqlite3
import subprocess
import pickle
import json
import tempfile
import logging
import stat
import platform
import re
import ast
from typing import Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Secrets should come from environment variables or a secret manager, not hardcoded.
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")

# Network helper with safe defaults
def get_api_data(endpoint: str, timeout: int = 5) -> Optional[str]:
    if not EXTERNAL_API_KEY:
        logger.error("Missing EXTERNAL_API_KEY in environment")
        return None
    headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
    try:
        r = requests.get(endpoint, headers=headers, timeout=timeout, verify=True)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        logger.error("Network request failed: %s", e)
        return None

# Use parameterized queries to prevent SQL injection and manage the connection using context managers.
def connect_db(db_path: str, username: Optional[str] = None, password: Optional[str] = None):
    username = username or DB_USER
    password = password or DB_PASS
    if not username or not password:
        raise ValueError("Database credentials not set in environment")
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        return cur.fetchone()

# Validate user input and avoid shell=True. Use platform-aware ping args.
_HOST_RE = re.compile(r"^[A-Za-z0-9\.-]+$")

def run_command(user_input: str):
    if not _HOST_RE.match(user_input):
        raise ValueError("Invalid host format")
    # Cross-platform basic ping
    count_flag = "-n" if platform.system().lower().startswith("win") else "-c"
    cmd = ["ping", count_flag, "1", user_input]
    # Do not use shell=True and capture output
    try:
        subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        logger.error("Command execution failed: %s", e)

# Safe deserialization: prefer JSON. Allow pickle only when explicitly enabled via env.
def load_user_profile(serialized_data: bytes):
    try:
        return json.loads(serialized_data.decode("utf-8"))
    except Exception:
        # Only allow pickle in controlled environments
        if os.getenv("ALLOW_PICKLE") == "1":
            return pickle.loads(serialized_data)
        raise ValueError("Untrusted serialized data: only JSON is allowed by default")

# Replace eval with ast.literal_eval for safety; limit to literals.
def eval_expression(expr: str):
    try:
        return ast.literal_eval(expr)
    except Exception as e:
        raise ValueError("Unsafe or invalid expression") from e

# Save secrets securely to a constrained directory with restrictive permissions. Prefer secret managers.
def save_secret_to_file(secret: str, path: str):
    base_dir = os.path.abspath("./secrets")
    os.makedirs(base_dir, exist_ok=True)
    dest = os.path.abspath(path)
    if not dest.startswith(base_dir):
        raise ValueError("Secrets must be saved inside the ./secrets directory")
    # Write securely
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    fd = os.open(dest, flags, 0o600)
    try:
        with os.fdopen(fd, "w") as f:
            f.write(secret)
    finally:
        try:
            os.chmod(dest, 0o600)
        except Exception:
            pass

# Load private key from environment or protected file path; do not store in source.
def get_private_key():
    pk = os.getenv("PRIVATE_KEY")
    if pk:
        return pk
    path = os.getenv("PRIVATE_KEY_PATH")
    if path and os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    raise ValueError("Private key not found in environment or path")

# Validate file paths and destination host before uploading. Use timeouts and verify SSL.
def upload_file(file_path: str, destination: str, timeout: int = 5):
    # Basic validation: no parent traversal outside current dir
    fp = os.path.abspath(file_path)
    base = os.path.abspath(".")
    if not fp.startswith(base):
        raise ValueError("Invalid file path")
    # Destination whitelist
    whitelist = os.getenv("UPLOAD_WHITELIST")
    if whitelist:
        allowed = [h.strip() for h in whitelist.split(",") if h.strip()]
        if not any(h in destination for h in allowed):
            raise ValueError("Destination not allowed")
    try:
        with open(fp, "rb") as f:
            data = f.read()
        r = requests.post(destination, data=data, timeout=timeout, verify=True)
        r.raise_for_status()
        return r.status_code
    except Exception as e:
        logger.error("Upload failed: %s", e)
        return None

# Avoid predictable temp file names and set correct permissions.
def insecure_temp_file_write(data: str):
    tf = tempfile.NamedTemporaryFile(delete=False, prefix="vuln_", dir=None, mode="w")
    try:
        tf.write(data)
        tf.flush()
    finally:
        tf.close()
    try:
        os.chmod(tf.name, 0o600)
    except Exception:
        pass
    return tf.name

if __name__ == "__main__":
    # When running tests, set SAFE_TEST=1 to avoid destructive actions
    SAFE_TEST = os.getenv("SAFE_TEST") == "1"
    print(get_api_data("https://api.example.com/data"))
    try:
        print(connect_db("example.db"))
    except Exception as e:
        logger.error("DB connect failed: %s", e)
    if not SAFE_TEST:
        try:
            run_command("example.com")
        except Exception as e:
            logger.error("Command failed: %s", e)
    try:
        print(load_user_profile(b"{\"name\": \"test\"}"))
    except Exception as e:
        logger.error("Deserialization failed: %s", e)
    try:
        print(eval_expression("{'a': 1}"))
    except Exception as e:
        logger.error("Eval failed: %s", e)
    try:
        save_secret_to_file("TOP_SECRET", "./secrets/secrets.txt")
    except Exception as e:
        logger.error("Saving secret failed: %s", e)
    try:
        # Only print key in safe environments (not recommended normally)
        if SAFE_TEST:
            try:
                print(get_private_key())
            except Exception:
                pass
    except Exception:
        pass
    try:
        if not SAFE_TEST:
            upload_file("./README.md", "https://upload.example.com/")
    except Exception as e:
        logger.error("Upload failed: %s", e)
    print(os.getenv("SERVICE_TOKEN"))
    print(insecure_temp_file_write("temporary data"))