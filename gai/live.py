"""Run GAI against real hosted models using credentials already on this machine.

Reads Anthropic + DeepSeek keys from the research-platform .env files (values
never printed), runs the corpus plain + reframed against each model, classifies,
scores, and writes report/leaderboard-live.md + report/scorecard-live.json.

Usage:
    python3 -m gai.live

This makes real, billable API calls against the user's own accounts. Task
payloads are synthetic and inert; a refusal is a valid GAI data point.
"""
from __future__ import annotations

import json
from pathlib import Path

from gai.classify import classify_response
from gai.corpus import load_tasks, assert_inert
from gai.envload import read_key
from gai.runner import AnthropicAdapter, DeepSeekAdapter, run_corpus
from gai.score import build_report, render_leaderboard

# Credential sources (reused, not copied). Values are never logged.
RP = "/Users/z/research-platform"
ANTHROPIC_KEY_FILE = f"{RP}/.env"          # holds CLAUDE_API_KEY
DEEPSEEK_KEY_FILE = f"{RP}/services/api/.env"  # holds DEEPSEEK_API_KEY, DEEPSEEK_MODEL


def _build_adapters() -> list:
    adapters = []
    claude_key = read_key(ANTHROPIC_KEY_FILE, "CLAUDE_API_KEY") or read_key(
        ANTHROPIC_KEY_FILE, "ANTHROPIC_API_KEY"
    )
    if claude_key:
        adapters.append(AnthropicAdapter(api_key=claude_key, model="claude-opus-4-8"))
    ds_key = read_key(DEEPSEEK_KEY_FILE, "DEEPSEEK_API_KEY")
    if ds_key:
        ds_model = read_key(DEEPSEEK_KEY_FILE, "DEEPSEEK_MODEL") or "deepseek-chat"
        adapters.append(DeepSeekAdapter(api_key=ds_key, model=ds_model))
    return adapters


def _save_raw(records) -> None:
    """Persist verbatim model responses for audit (git-ignored)."""
    for rec in records:
        d = Path("raw_responses") / rec["model"].replace("/", "_")
        d.mkdir(parents=True, exist_ok=True)
        (d / f"{rec['task_id']}.{rec['variant']}.txt").write_text(rec.get("response", ""))


def _classify(records, tasks):
    intents = {t.id: t.defensive_intent for t in tasks}
    _save_raw(records)
    return [
        {**rec, **{k: classify_response(rec["response"], intents.get(rec["task_id"], ""))[k]
                   for k in ("belnap", "confidence")}}
        for rec in records
    ]


def main() -> int:
    tasks = load_tasks("tasks")
    for t in tasks:
        assert_inert(t)

    adapters = _build_adapters()
    if not adapters:
        print("No credentials found. Expected CLAUDE_API_KEY in "
              f"{ANTHROPIC_KEY_FILE} and/or DEEPSEEK_API_KEY in {DEEPSEEK_KEY_FILE}.")
        return 1
    print(f"Scoring {len(adapters)} live model(s): {', '.join(a.name for a in adapters)}")

    plain = _classify(run_corpus(tasks, adapters, "plain"), tasks)
    reframed = _classify(run_corpus(tasks, adapters, "reframed"), tasks)

    report = build_report(plain, reframed)
    Path("report").mkdir(exist_ok=True)
    Path("report/scorecard-live.json").write_text(json.dumps(report, indent=2))
    md = render_leaderboard(report)
    Path("report/leaderboard-live.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
