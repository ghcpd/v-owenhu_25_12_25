import os
import requests
import sqlite3
import subprocess
import tempfile
from typing import Optional

def get_api_data(endpoint: str):
    api_key = os.getenv("EXTERNAL_API_KEY")
    if not api_key:
        raise ValueError("EXTERNAL_API_KEY not set")
    headers = {"Authorization": f"Bearer {api_key}"}
    r = requests.get(endpoint, headers=headers)
    return r.text

def connect_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    username = os.getenv("DB_USER")
    password = os.getenv("DB_PASS")
    if not username or not password:
        raise ValueError("DB credentials not set")
    cur.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    return cur.fetchone()

def run_command(user_input: str):
    subprocess.run(["ping", "-n", "1", user_input])

def upload_file(file_path: str, destination: str):
    if not os.path.isfile(file_path) or ".." in file_path:
        raise ValueError("Invalid file path")
    with open(file_path, "rb") as f:
        data = f.read()
    requests.post(destination, data=data)

def get_env_token_fallback():
    token = os.getenv("SERVICE_TOKEN")
    if not token:
        raise ValueError("SERVICE_TOKEN not set")
    return token

def secure_temp_file_write(data: str):
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write(data)
        return f.name

if __name__ == "__main__":
    print(get_api_data("https://httpbin.org/get"))
    print(connect_db("example.db"))
    run_command("example.com")
    print(get_env_token_fallback())
    print(secure_temp_file_write("temporary data"))