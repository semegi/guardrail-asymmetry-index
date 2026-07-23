"""Minimal .env key loader.

Reads a single KEY=value from a dotenv-style file and returns the value.
Never logs or prints the value — callers pass it straight into an adapter.
Used to reuse credentials already configured elsewhere on the machine
(e.g. research-platform's .env files) without copying secrets around.
"""
from __future__ import annotations

import os
from pathlib import Path


def read_key(path: str, key: str) -> str | None:
    """Return the value of `key` from a dotenv file, or None if absent.

    Precedence: a real environment variable of the same name wins over the file.
    Strips surrounding quotes. Does not expand or interpolate.
    """
    env_val = os.environ.get(key)
    if env_val:
        return env_val
    f = Path(path)
    if not f.exists():
        return None
    for line in f.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() == key:
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
                v = v[1:-1]
            return v or None
    return None
