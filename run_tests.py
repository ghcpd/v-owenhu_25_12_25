#!/usr/bin/env python3
"""Static & lightweight behavioral tests for this kata.

Usage: python run_tests.py [target_file]
- Returns exit code 0 if the target_file is considered SECURE (no risky patterns)
- Returns exit code 1 if risky patterns were found

This script is safe to run (it does not execute untrusted code from the
target files) — it performs regex/AST checks and small non-destructive
sanity checks only.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from typing import List

PATTERNS = [
    (r"EXTERNAL_API_KEY\s*=\s*[\'\"]", "hardcoded API key (literal assignment)"),
    (r"DB_PASS\s*=\s*[\'\"]|DB_USER\s*=\s*[\'\"]", "hardcoded DB credentials (literal assignment)"),
    (r"verify\s*=\s*False", "requests called with verify=False"),
    (r"pickle\.loads\(", "unsafe deserialization (pickle.loads)"),
    (r"\beval\(", "use of eval()"),
    (r"subprocess\.call\(", "subprocess.call usage (possible shell invocation)"),
    (r"f\"?SELECT\s+.*username", "possible SQL built with f-string (SQL injection)"),
    (r"DEFAULT_TOKEN_IN_CODE", "hardcoded default token"),
    (r"[\'\"]?/tmp/vuln_temp\.txt[\'\"]", "predictable temporary file path"),
    (r"-----BEGIN RSA PRIVATE KEY-----", "hardcoded private key material"),
    (r"requests\.post\([^\)]*\.\./etc/passwd", "attempt to exfiltrate filesystem")
]


def load_source(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def run_static_checks(source: str) -> List[str]:
    issues: List[str] = []
    for pat, desc in PATTERNS:
        if re.search(pat, source):
            issues.append(desc)
    return issues


def run_ast_checks(source: str) -> List[str]:
    issues: List[str] = []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        issues.append("syntax error when parsing (could be malicious)")
        return issues

    for node in ast.walk(tree):
        # detect formatted SQL using f-strings
        if isinstance(node, ast.JoinedStr):
            s = ast.get_source_segment(source, node) or ""
            if re.search(r"SELECT\s+.*username", s, re.I):
                issues.append("f-string used to build SQL-like expression")

        # detect use of pickle, eval
        if isinstance(node, ast.Call) and getattr(node.func, "id", "") == "eval":
            issues.append("use of eval() (AST)")
        if isinstance(node, ast.Call) and getattr(node.func, "attr", "") == "loads":
            if getattr(node.func, "value", None) and getattr(node.func.value, "id", "") == "pickle":
                issues.append("pickle.loads() usage (AST)")

        # detect subprocess calls that set shell=True (AST - avoids matching docstrings)
        if isinstance(node, ast.Call):
            for kw in getattr(node, "keywords", []):
                if getattr(kw, "arg", None) == "shell":
                    val = getattr(kw, "value", None)
                    if isinstance(val, ast.Constant) and val.value is True:
                        issues.append("subprocess invoked with shell=True (AST)")
            # detect direct calls to subprocess.call/run
            func = node.func
            if isinstance(func, ast.Attribute) and getattr(func.value, "id", "") == "subprocess":
                if func.attr in ("call", "run"):
                    # only flag subprocess when the first positional arg is a string
                    first_arg = node.args[0] if node.args else None
                    if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                        issues.append("subprocess called with a string command (possible shell invocation)")

    return issues


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("target", nargs="?", default="input.py", help="file to test")
    args = p.parse_args(argv)

    path = args.target
    if not os.path.exists(path):
        print(f"ERROR: {path} not found")
        return 2

    src = load_source(path)
    static_issues = run_static_checks(src)
    ast_issues = run_ast_checks(src)

    issues = sorted(set(static_issues + ast_issues))

    result = {
        "file": path,
        "checked": len(PATTERNS),
        "issues_found": len(issues),
        "issues": issues,
    }

    print(json.dumps(result, indent=2))

    # exit code: 0 == secure (no issues), 1 == vulnerable
    return 0 if len(issues) == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
