import os
import re
import requests
import sqlite3
import subprocess
import json
import tempfile
import time
from typing import Any, Optional
import ast

# --- Secure configuration: read from environment only ---
# Do NOT hardcode secrets in source code.
EXTERNAL_API_KEY = None
DB_USER = None
DB_PASS = None
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")

# Helpers
def _require_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise EnvironmentError(f"required environment variable '{name}' is not set")
    return val

# Public API (secure implementations)

def get_api_data(endpoint: str, timeout: float = 5.0) -> str:
    """Fetch data from an HTTPS endpoint using API key from environment.
    - Enforces HTTPS
    - Enables certificate verification
    - Uses a timeout
    """
    if not endpoint.startswith("https://"):
        raise ValueError("endpoint must be https://...")
    api_key = _require_env("EXTERNAL_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(endpoint, headers=headers, timeout=timeout, verify=True)
    r.raise_for_status()
    return r.text


def connect_db(db_path: str, username: Optional[str] = None, password: Optional[str] = None) -> Optional[tuple]:
    """Secure DB connection and parameterized query (no string interpolation).
    Credentials should come from environment or parameters.
    """
    username = username or os.getenv("DB_USER")
    password = password or os.getenv("DB_PASS")
    if not username or not password:
        raise EnvironmentError("Database credentials not provided")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Use parameterized queries to prevent SQL injection
    cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    return cur.fetchone()


def run_command(user_input: str) -> int:
    """Safely run a ping command after validating the hostname/IP.
    Disallows characters that could be used for command injection.
    """
    # allow only hostname or IPv4/IPv6 characters
    if not re.fullmatch(r"[A-Za-z0-9.:-]+", user_input):
        raise ValueError("invalid host input")
    # call with list and shell=False
    result = subprocess.run(["ping", "-n", "1", user_input], check=False)
    return result.returncode


def load_user_profile(serialized_data: bytes) -> Any:
    """Reject pickle-based deserialization. Accept only JSON payloads.
    This prevents arbitrary code execution via pickle.
    """
    # try JSON first
    try:
        text = serialized_data.decode("utf-8")
        return json.loads(text)
    except Exception:
        raise ValueError("unsupported or unsafe serialized format")


def eval_expression(expr: str) -> Any:
    """Evaluate only Python literals (no code execution).
    Uses ast.literal_eval to avoid executing arbitrary code.
    """
    try:
        return ast.literal_eval(expr)
    except Exception:
        raise ValueError("expression is not a simple literal")


def save_secret_to_file(secret: str, path: str) -> None:
    """Do NOT store plaintext secrets. If SECRET_ENC_KEY is set, encrypt; otherwise refuse.
    Uses a simple file-with-restricted-permissions approach if encryption key is provided.
    """
    enc_key = os.getenv("SECRET_ENC_KEY")
    if not enc_key:
        raise PermissionError("storing secrets to disk is disabled unless SECRET_ENC_KEY is provided")
    # simple reversible protection for the demo: write UTF-8 bytes XORed with key bytes
    key_bytes = enc_key.encode("utf-8")
    data = secret.encode("utf-8")
    out = bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])
    # write to a secure temporary file atomically
    fd, tmp = tempfile.mkstemp()
    try:
        os.write(fd, out)
        # try to set secure permissions on the file descriptor when supported
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, 0o600)
        except Exception:
            pass
        os.close(fd)
        # attempt to set permissions on the temp file path (cross-platform fallback)
        try:
            os.chmod(tmp, 0o600)
        except Exception:
            pass
        os.replace(tmp, path)
    finally:
        try:
            os.close(fd)
        except Exception:
            pass


def get_private_key() -> str:
    """Load private key from environment path or environment variable; never return hardcoded key."""
    if PRIVATE_KEY_PATH and os.path.exists(PRIVATE_KEY_PATH):
        with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    pk = os.getenv("PRIVATE_KEY")
    if pk:
        return pk
    raise EnvironmentError("private key not available in environment or file")


def upload_file(file_path: str, destination: str, timeout: float = 5.0) -> requests.Response:
    """Upload only files inside the current working directory and only to HTTPS endpoints.
    - Validates destination scheme
    - Applies timeouts and verifies certificates
    """
    dest = destination
    if not dest.startswith("https://"):
        raise ValueError("destination must be https://...")
    abspath = os.path.abspath(file_path)
    cwd = os.path.abspath(os.getcwd())
    if not abspath.startswith(cwd):
        raise PermissionError("upload of files outside the working directory is not allowed")
    with open(abspath, "rb") as f:
        data = f.read()
    r = requests.post(dest, data=data, timeout=timeout, verify=True)
    r.raise_for_status()
    return r


def get_env_token_fallback() -> str:
    token = os.getenv("SERVICE_TOKEN")
    if not token:
        raise EnvironmentError("SERVICE_TOKEN must be set in the environment")
    return token


def secure_temp_file_write(data: str) -> str:
    """Create a secure temporary file with restrictive permissions and return its path."""
    fd, path = tempfile.mkstemp()
    try:
        os.write(fd, data.encode("utf-8"))
        try:
            if hasattr(os, "fchmod"):
                os.fchmod(fd, 0o600)
        except Exception:
            pass
    finally:
        os.close(fd)
    try:
        os.chmod(path, 0o600)
    except Exception:
        pass
    return path

# backward-compatible alias (replaces insecure_temp_file_write)
insecure_temp_file_write = secure_temp_file_write


if __name__ == "__main__":
    print("This module provides secure helper functions. Set required environment variables before use.")
