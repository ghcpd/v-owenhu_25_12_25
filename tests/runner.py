import importlib.util
import sys
import os
import pickle


def load_module_from_path(path: str):
    spec = importlib.util.spec_from_file_location("target_module", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fail(msg: str):
    print("FAIL:", msg)
    sys.exit(1)


def ok(msg: str):
    print("OK:", msg)


def run_checks(path: str):
    mod = load_module_from_path(path)

    # 1) Hardcoded API key must not be present
    api_key = getattr(mod, "EXTERNAL_API_KEY", None)
    if isinstance(api_key, str) and api_key.strip():
        fail("hardcoded EXTERNAL_API_KEY detected")
    ok("no hardcoded EXTERNAL_API_KEY")

    # 2) eval_expression must not execute arbitrary code
    try:
        res = mod.eval_expression("__import__('os').getcwd()")
        # if it returned a string, eval executed — vulnerable
        if isinstance(res, str):
            fail("eval_expression executed arbitrary code")
    except Exception:
        ok("eval_expression is safe")

    # 3) load_user_profile must reject pickle-based payloads
    try:
        payload = pickle.dumps({"p": "x"})
        r = mod.load_user_profile(payload)
        # secure implementation should not accept pickle
        fail("load_user_profile accepted pickle data")
    except Exception:
        ok("load_user_profile rejects pickle/deserialization attacks")

    # 4) run_command must validate input
    try:
        mod.run_command("example.com; echo hacked")
        fail("run_command did not validate input (possible command injection)")
    except Exception:
        ok("run_command input validation in place")

    # 5) get_env_token_fallback should not return hardcoded default
    try:
        # Ensure SERVICE_TOKEN is not set in environment for this test
        os.environ.pop("SERVICE_TOKEN", None)
        t = mod.get_env_token_fallback()
        fail("get_env_token_fallback returned a hardcoded fallback token")
    except Exception:
        ok("get_env_token_fallback enforces environment configuration")

    # 6) insecure_temp_file_write should not use a predictable /tmp path
    try:
        p = mod.insecure_temp_file_write("data")
        if p == "/tmp/vuln_temp.txt":
            fail("insecure_temp_file_write used a predictable path")
        ok("insecure_temp_file_write uses secure temporary file")
    except Exception as e:
        fail(f"insecure_temp_file_write failed: {e}")

    print("All checks passed for", path)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: runner.py <path-to-module>")
        sys.exit(2)
    run_checks(sys.argv[1])