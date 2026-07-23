"""Task corpus: schema, loader, and inertness lint."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_REQUIRED = ("id", "prompt", "defensive_intent", "benign_reframing", "expected_capability")

_URL = re.compile(r"https?://", re.I)
_PUBLIC_IP = re.compile(r"\b(?!10\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.)"
                        r"(?:\d{1,3}\.){3}\d{1,3}\b")
_LIVE_DOMAIN = re.compile(r"\b[a-z0-9-]+\.(?:com|net|org|io|co|ru|cn)\b", re.I)
_ALLOWED_DOMAIN = re.compile(r"\bdataset\.example\b|\bexample\.(?:com|org|net)\b", re.I)


@dataclass
class Task:
    id: str
    prompt: str
    defensive_intent: str
    benign_reframing: str
    expected_capability: str


def load_tasks(path: str = "tasks") -> list:
    tasks = []
    for f in sorted(Path(path).glob("*.json")):
        data = json.loads(f.read_text())
        missing = [k for k in _REQUIRED if k not in data]
        if missing:
            raise ValueError(f"{f.name} missing fields: {missing}")
        tasks.append(Task(**{k: data[k] for k in _REQUIRED}))
    return tasks


def assert_inert(task: Task) -> None:
    blob = f"{task.prompt}\n{task.benign_reframing}"
    if _URL.search(blob):
        raise ValueError(f"task {task.id}: contains a live URL")
    if _PUBLIC_IP.search(blob):
        raise ValueError(f"task {task.id}: contains a public IP")
    stripped = _ALLOWED_DOMAIN.sub("", blob)
    if _LIVE_DOMAIN.search(stripped):
        raise ValueError(f"task {task.id}: contains a live-looking domain")
