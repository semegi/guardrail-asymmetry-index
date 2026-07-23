"""Re-score already-captured raw responses with the model-judge classifier.

Reuses raw_responses/<model>/<task>.<variant>.txt from a prior `gai.live` run —
no target-model calls, only judge calls. Writes report/leaderboard-judged.md.
This is the trustworthy scoring path; the keyword heuristic (gai.classify) is
kept for offline/CI use where no judge is available.
"""
from __future__ import annotations

import json
from pathlib import Path

from gai.corpus import load_tasks, assert_inert
from gai.envload import read_key
from gai.judge import ModelJudgeClassifier
from gai.runner import AnthropicAdapter
from gai.score import build_report, render_leaderboard
from gai.live import ANTHROPIC_KEY_FILE

RAW = Path("raw_responses")


def _load_records() -> list:
    records = []
    for model_dir in sorted(RAW.iterdir()):
        if not model_dir.is_dir():
            continue
        for f in sorted(model_dir.glob("*.txt")):
            task_id, variant, _ = f.name.split(".")  # 001.plain.txt
            records.append({"model": model_dir.name, "task_id": task_id,
                            "variant": variant, "response": f.read_text()})
    return records


def main() -> int:
    if not RAW.exists():
        print("No raw_responses/ found — run `python3 -m gai.live` first.")
        return 1
    tasks = load_tasks("tasks")
    for t in tasks:
        assert_inert(t)
    intents = {t.id: t.defensive_intent for t in tasks}

    key = read_key(ANTHROPIC_KEY_FILE, "CLAUDE_API_KEY") or read_key(
        ANTHROPIC_KEY_FILE, "ANTHROPIC_API_KEY")
    if not key:
        print("No Anthropic key for the judge.")
        return 1
    judge = ModelJudgeClassifier(AnthropicAdapter(api_key=key, model="claude-opus-4-8"))

    records = _load_records()
    print(f"Judging {len(records)} responses with claude-opus-4-8 ...")
    judged = []
    for rec in records:
        c = judge.classify(rec["response"], intents.get(rec["task_id"], ""))
        judged.append({**rec, "belnap": c["belnap"]})

    plain = [r for r in judged if r["variant"] == "plain"]
    reframed = [r for r in judged if r["variant"] == "reframed"]
    report = build_report(plain, reframed)
    Path("report").mkdir(exist_ok=True)
    Path("report/scorecard-judged.json").write_text(json.dumps(report, indent=2))
    md = render_leaderboard(report)
    Path("report/leaderboard-judged.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
