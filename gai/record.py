"""Score real, pre-captured model transcripts under transcripts/<model>/<task_id>.txt.

Usage:
    python3 -m gai.record                 # scores every model dir under transcripts/
    python3 -m gai.record modelA modelB   # scores only the named model dirs

Produces report/leaderboard-real.md and report/scorecard-real.json. No network,
no API keys — the honest bridge from stub demos to real model data. Add a model by
dropping its verbatim responses in transcripts/<model>/<task_id>.txt.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from gai.classify import classify_response
from gai.corpus import load_tasks, assert_inert
from gai.runner import RecordedAdapter, run_recorded
from gai.score import build_report, render_leaderboard

TRANSCRIPTS = "transcripts"


def _discover_models(root: str) -> list:
    base = Path(root)
    if not base.exists():
        return []
    return sorted(p.name for p in base.iterdir() if p.is_dir())


def _classify_records(records, tasks):
    intents = {t.id: t.defensive_intent for t in tasks}
    out = []
    for rec in records:
        c = classify_response(rec["response"], intents.get(rec["task_id"], ""))
        out.append({**rec, "belnap": c["belnap"], "confidence": c["confidence"]})
    return out


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    tasks = load_tasks("tasks")
    for t in tasks:
        assert_inert(t)

    models = argv or _discover_models(TRANSCRIPTS)
    if not models:
        print(f"No transcripts found under {TRANSCRIPTS}/. "
              f"Add {TRANSCRIPTS}/<model>/<task_id>.txt files (task ids: "
              f"{', '.join(t.id for t in tasks)}).")
        return 1

    adapters = [RecordedAdapter(name=m, root=TRANSCRIPTS) for m in models]
    plain = _classify_records(run_recorded(tasks, adapters, "plain"), tasks)
    report = build_report(plain, reframed=[])  # plain-only real data; no jailbreak variant yet

    Path("report").mkdir(exist_ok=True)
    Path("report/scorecard-real.json").write_text(json.dumps(report, indent=2))
    md = render_leaderboard(report)
    Path("report/leaderboard-real.md").write_text(md)
    print(md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
