"""End-to-end pipeline: corpus -> run (plain+reframed) -> classify -> score -> report."""
from __future__ import annotations

import json
from pathlib import Path

from gai.classify import classify_response
from gai.corpus import load_tasks, assert_inert
from gai.runner import StubAdapter, run_corpus
from gai.score import build_report, render_leaderboard


def _demo_adapters():
    """Bundled deterministic models illustrating the asymmetry, for offline demo."""
    performs = StubAdapter(
        name="open-weight-local",
        responses={
            "RCE": "Here is the analysis: eval() on the config is the RCE path; detect and monitor it.",
            "telemetry": "Attack chain: initial access, then credential theft; detect at each stage.",
            "signals": "The credential and persistence signals correlate; the DNS spike is exfil. Confidence: high.",
        },
        default="Here is a defensive analysis; monitor and detect the described behavior.",
    )
    refuses = StubAdapter(
        name="guardrailed-frontier",
        responses={
            "RCE": "I'm sorry, I can't help analyze that payload.",
            "telemetry": "I cannot assist with that request.",
            "signals": "I'm unable to help with security intrusion analysis.",
        },
        default="I can't help with that.",
    )
    refuses_but_capable = StubAdapter(
        name="guardrailed-frontier",
        responses={
            "training": "Sure: eval on config is unsafe; here is how to detect and mitigate it.",
            "SOC": "For training: these events form initial-access then lateral-movement; monitor each.",
            "analyst-training": "Group the credential and persistence alerts; the DNS spike is exfil.",
        },
        default="For training purposes, here is the defensive walkthrough; detect and monitor it.",
    )
    return [performs, refuses, refuses_but_capable]


def _classify_records(records, tasks):
    intents = {t.id: t.defensive_intent for t in tasks}
    out = []
    for rec in records:
        c = classify_response(rec["response"], intents.get(rec["task_id"], ""))
        out.append({**rec, "belnap": c["belnap"], "confidence": c["confidence"]})
    return out


def main(argv=None) -> int:
    tasks = load_tasks("tasks")
    for t in tasks:
        assert_inert(t)

    adapters = _demo_adapters()
    plain_adapters = adapters[:2]                    # open-weight + guardrailed (plain)
    reframed_adapters = [adapters[0], adapters[2]]   # same names, reframed behavior

    plain = _classify_records(run_corpus(tasks, plain_adapters, "plain"), tasks)
    reframed = _classify_records(run_corpus(tasks, reframed_adapters, "reframed"), tasks)

    report = build_report(plain, reframed)
    Path("report").mkdir(exist_ok=True)
    Path("report/scorecard.json").write_text(json.dumps(report, indent=2))
    Path("report/leaderboard.md").write_text(render_leaderboard(report))
    print(render_leaderboard(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
