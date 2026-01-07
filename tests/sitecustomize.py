import os

# Test harness: when SAFE_TEST=1 is set, patch dangerous operations to safe stubs.
if os.getenv('SAFE_TEST') == '1':
    # Lightweight stubs avoiding network and system side-effects
    class DummyResponse:
        def __init__(self, text='', status_code=200):
            self.text = text
            self.status_code = status_code
        def raise_for_status(self):
            if not (200 <= self.status_code < 300):
                raise Exception('HTTP error')

    import sys
    import requests as _real_requests
    def _safe_get(*args, **kwargs):
        return DummyResponse(text='SAFE_TEST_RESPONSE')
    def _safe_post(*args, **kwargs):
        return DummyResponse(text='OK', status_code=200)
    _real_requests.get = _safe_get
    _real_requests.post = _safe_post

    import subprocess as _real_subprocess
    def _safe_run(*args, **kwargs):
        class R:
            returncode = 0
            stdout = b''
            stderr = b''
        return R()
    _real_subprocess.run = _safe_run

    import pickle as _real_pickle
    def _safe_loads(data):
        raise ValueError('pickle.loads is disabled in SAFE_TEST mode')
    _real_pickle.loads = _safe_loads

    # Prevent writing secrets outside of ./secrets
    _orig_open = open
    def _safe_open(path, mode='r', *args, **kwargs):
        if 'w' in mode or 'a' in mode:
            allowed_prefix = os.path.abspath('./secrets')
            if not os.path.abspath(path).startswith(allowed_prefix):
                raise PermissionError('Write disallowed in SAFE_TEST mode')
        return _orig_open(path, mode, *args, **kwargs)
    __builtins__['open'] = _safe_open
