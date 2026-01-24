import os
import requests
import sqlite3
import subprocess
import pickle
import base64
from typing import Optional

EXTERNAL_API_KEY = "ABC123_SUPER_SECRET_API_KEY"
DB_USER = "admin"
DB_PASS = "P@ssw0rd!"

def get_api_data(endpoint: str):
    headers = {"Authorization": f"Bearer {EXTERNAL_API_KEY}"}
    r = requests.get(endpoint, headers=headers, verify=False)
    return r.text

def connect_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    username = DB_USER
    password = DB_PASS
    cur.execute(f"SELECT id FROM users WHERE username = '{username}' AND password = '{password}'")
    return cur.fetchone()

def run_command(user_input: str):
    cmd = f"ping -n 1 {user_input}"
    subprocess.call(cmd, shell=True)

def load_user_profile(serialized_data: bytes):
    profile = pickle.loads(serialized_data)
    return profile

def eval_expression(expr: str):
    return eval(expr)

def save_secret_to_file(secret: str, path: str):
    with open(path, "w") as f:
        f.write(secret)

def get_private_key():
    private_key = """-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQC7...
-----END RSA PRIVATE KEY-----"""
    return private_key

def upload_file(file_path: str, destination: str):
    with open(file_path, "rb") as f:
        data = f.read()
    requests.post(destination, data=data)

def get_env_token_fallback():
    token = os.getenv("SERVICE_TOKEN")
    if not token:
        token = "DEFAULT_TOKEN_IN_CODE"
    return token

def insecure_temp_file_write(data: str):
    tmp_path = "/tmp/vuln_temp.txt"
    with open(tmp_path, "w") as f:
        f.write(data)
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
