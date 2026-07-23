"""Runner and model adapters. Only OllamaAdapter performs external I/O."""
from __future__ import annotations

import json
import urllib.request
from typing import Protocol, runtime_checkable

from gai.corpus import Task


@runtime_checkable
class ModelAdapter(Protocol):
    name: str

    def generate(self, prompt: str) -> str: ...


class StubAdapter:
    """Deterministic adapter: first response whose key is a substring of the prompt."""

    def __init__(self, name: str, responses: dict, default: str = "") -> None:
        self.name = name
        self._responses = responses
        self._default = default

    def generate(self, prompt: str) -> str:
        for key, resp in self._responses.items():
            if key in prompt:
                return resp
        return self._default


class OllamaAdapter:
    """Local open-weight adapter via Ollama HTTP API. Not used in tests."""

    def __init__(self, model: str, host: str = "http://localhost:11434") -> None:
        self.name = model
        self._model = model
        self._host = host.rstrip("/")

    def generate(self, prompt: str) -> str:
        payload = json.dumps(
            {"model": self._model, "prompt": prompt, "stream": False}
        ).encode()
        req = urllib.request.Request(
            f"{self._host}/api/generate", data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=120) as r:  # noqa: S310 (local host)
            return json.loads(r.read()).get("response", "")


def run_corpus(tasks: list, adapters: list, variant: str = "plain") -> list:
    records = []
    for adapter in adapters:
        for task in tasks:
            prompt = task.prompt if variant == "plain" else task.benign_reframing
            rec = {"model": adapter.name, "task_id": task.id, "variant": variant}
            try:
                rec["response"] = adapter.generate(prompt)
            except Exception as exc:  # capture, never crash the batch
                rec["response"] = ""
                rec["error"] = str(exc)
            records.append(rec)
    return records
