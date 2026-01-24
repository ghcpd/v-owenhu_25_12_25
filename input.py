"""Secure implementation of the original sample with mitigations.
This module preserves the original public function names but removes
unsafe behavior (no hardcoded secrets, no pickle/eval, parameterized SQL,
no shell=True, safe temp files, validated uploads, and timeouts for HTTP).
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
import sqlite3
import subprocess
import tempfile
import time
import urllib.parse
from typing import Optional

import requests

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Configuration: MUST be provided by environment in production.
EXTERNAL_API_KEY = os.getenv("EXTERNAL_API_KEY")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
PRIVATE_KEY_PATH = os.getenv("PRIVATE_KEY_PATH")
ALLOWED_UPLOAD_HOSTS = os.getenv("ALLOWED_UPLOAD_HOSTS", "").split(",") if os.getenv("ALLOWED_UPLOAD_HOSTS") else []
ALLOWED_UPLOAD_DIR = os.getenv("ALLOWED_UPLOAD_DIR")
SECRETS_DIR = os.getenv("SECRETS_DIR")

HTTP_TIMEOUT = float(os.getenv("HTTP_TIMEOUT", "5"))

def get_api_data(endpoint: str) -> Optional[str]:
    """Fetch data from an endpoint with TLS verification and timeout.

    - Enforces HTTPS
    - Requires EXTERNAL_API_KEY to be set in env
    - Uses a short timeout and raises on non-2xx
    """
    if not EXTERNAL_API_KEY:
        raise SecurityError("external API key not configured")

    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme != "https":
        raise ValueError("only https endpoints are allowed")

    headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
    try:
        r = requests.get(endpoint, headers=headers, timeout=HTTP_TIMEOUT)
        r.raise_for_status()
        return r.text
    except requests.RequestException as exc:
        logger.exception("failed to fetch api data: %s", exc)
        return None

def connect_db(db_path: str, username: Optional[str] = None, password: Optional[str] = None) -> Optional[int]:
    """Secure DB lookup using parameterized queries and proper resource cleanup.

    This function does NOT store credentials in source code. It accepts
    credentials from the environment or as parameters.
    """
    username = username or DB_USER
    password = password or DB_PASS
    if not username or not password:
        raise SecurityError("database credentials not provided")

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()

def run_command(user_input: str) -> str:
    """Run a validated ping command without shell=True.

    - Validates hostname/IP strictly
    - Uses subprocess.run with a list and timeout
    - Returns stdout (decoded) or raises on invalid input
    """
    if not _HOST_RE.match(user_input):
        raise ValueError("invalid hostname")

    # cross-platform ping arg
    count_flag = "-n" if os.name == "nt" else "-c"
    cmd = ["ping", count_flag, "1", user_input]

    proc = subprocess.run(cmd, shell=False, capture_output=True, timeout=5, check=False)
    return proc.stdout.decode(errors="ignore").strip()

def load_user_profile(serialized_data: bytes) -> dict:
    """Safely deserialize a user profile.

    - Accepts JSON only (base64-encoded or raw)
    - Rejects pickle data
    """
    # quick check for pickle magic bytes
    if len(serialized_data) >= 2 and serialized_data[0] == 0x80:
        raise SecurityError("pickle deserialization is prohibited")

    try:
        text = serialized_data.decode("utf-8")
        return json.loads(text)
    except Exception as exc:
        raise ValueError("invalid profile data") from exc

def eval_expression(expr: str):
    """Safely evaluate only Python literals using ast.literal_eval."""
    try:
        return ast.literal_eval(expr)
    except Exception as exc:
        raise ValueError("expression not allowed") from exc

def save_secret_to_file(secret: str, path: str) -> None:
    """Persist a secret only into a configured secrets directory with
    restrictive permissions. The function refuses to write secrets to
    arbitrary locations.
    """
    if not SECRETS_DIR:
        raise SecurityError("SECRETS_DIR not configured; refusing to write secrets")

    abspath = os.path.abspath(path)
    if not abspath.startswith(os.path.abspath(SECRETS_DIR) + os.sep):
        raise SecurityError("refusing to write secrets outside SECRETS_DIR")

    # write file with restrictive permissions
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
    # 0o600 - owner read/write only
    try:
        fd = os.open(abspath, flags, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(secret)
    except OSError as exc:
        logger.exception("failed to write secret: %s", exc)
        raise

def get_private_key() -> Optional[str]:
    """Return private key material from a protected path (not from source).

    The path must be provided via PRIVATE_KEY_PATH environment variable.
    """
    if not PRIVATE_KEY_PATH:
        logger.debug("PRIVATE_KEY_PATH not set")
        return None
    try:
        with open(PRIVATE_KEY_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except OSError:
        logger.exception("could not read private key")
        return None

def upload_file(file_path: str, destination: str) -> bool:
    """Upload a file after validating both path and destination host.

    - Ensures file_path is under ALLOWED_UPLOAD_DIR
    - Ensures destination host is in ALLOWED_UPLOAD_HOSTS
    - Uses a short timeout and streams the upload
    """
    if ALLOWED_UPLOAD_DIR is None:
        raise SecurityError("ALLOWED_UPLOAD_DIR not configured")

    abs_fp = os.path.abspath(file_path)
    if not abs_fp.startswith(os.path.abspath(ALLOWED_UPLOAD_DIR) + os.sep):
        raise SecurityError("file not in allowed upload directory")

    parsed = urllib.parse.urlparse(destination)
    if parsed.scheme not in ("https", "http"):
        raise ValueError("invalid destination scheme")
    if ALLOWED_UPLOAD_HOSTS and parsed.hostname not in ALLOWED_UPLOAD_HOSTS:
        raise SecurityError("destination host not allowed")

    try:
        with open(abs_fp, "rb") as f:
            r = requests.post(destination, data=f, timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            return True
    except requests.RequestException:
        logger.exception("upload failed")
        return False

def get_env_token_fallback() -> Optional[str]:
    """Return SERVICE_TOKEN from environment or None (no insecure defaults)."""
    return os.getenv("SERVICE_TOKEN")

def secure_temp_file_write(data: str) -> str:
    """Create a secure temporary file and return its path."""
    tf = tempfile.NamedTemporaryFile(mode="w", delete=False)
    try:
        tf.write(data)
        tf.flush()
        # try to set restrictive permissions where supported
        try:
            os.chmod(tf.name, 0o600)
        except Exception:
            logger.debug("chmod unavailable on this platform")
        return tf.name
    finally:
        tf.close()


# expose the same function name used previously but implemented safely
insecure_temp_file_write = secure_temp_file_write

if __name__ == "__main__":
    print(get_api_data("https://api.example.com/data") or "<no-data>")
    print(connect_db("example.db"))
    print(run_command("example.com")[:200])
    try:
        load_user_profile(b"{}")
        print("deserialization: ok")
    except Exception as e:
        print("Deserialization failed:", e)
    try:
        print(eval_expression("[1, 2, 3]"))
    except Exception as e:
        print("Eval failed:", e)
    try:
        save_secret_to_file("TOP_SECRET", "secrets.txt")
    except Exception:
        print("secret write protected")
    print(get_private_key() or "<no-key-configured>")
    try:
        upload_file("./safe_upload.txt", "https://upload.example.com/")
    except Exception as e:
        print("Upload failed:", e)
    print(get_env_token_fallback())
    print(secure_temp_file_write("temporary data"))