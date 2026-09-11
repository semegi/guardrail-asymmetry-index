# What's in this directory

These files are **generated output**. Each is written by a different entry point, against a
different data source. Read this before quoting a number from any of them.

| File | Produced by | Models | Real data? |
|---|---|---|---|
| `leaderboard.md` | `gai.cli` | `open-weight-local`, `guardrailed-frontier` | **No — synthetic stubs.** A demo of the pipeline's shape, not a measurement. The dramatic spread is hand-authored fixture data. |
| `leaderboard-live.md` | `gai.live` | claude-opus-4-8, deepseek-chat | Yes — real API calls, scored by the **keyword heuristic**. Contains the known false positive (Claude 0.75, 1 suppressed). Retained deliberately as the "before" half of the correction. |
| `leaderboard-judged.md` | `gai.rejudge` | claude-opus-4-8, deepseek-chat | Yes — the **same captured responses**, re-scored by the model judge. This is the trustworthy result. |
| `leaderboard-real.md` | `gai.record` | claude-fable-5 | Yes — scored from a pasted verbatim transcript, no API key needed. Worked example of the zero-infrastructure path. |

## Which number is the real one

`leaderboard-judged.md`. Both models score GAI 1.00 with zero suppressed tasks: **no
guardrail lockout in this sample** (n = 3 tasks, 2 models).

`leaderboard-live.md` is kept alongside it on purpose. The difference between the two files
*is* the finding written up in
[`../docs/findings/2026-07-23-first-live-run.md`](../docs/findings/2026-07-23-first-live-run.md) —
a brittle classifier produced a spurious asymmetry signal, the warrant check flagged it as
unreproducible (`costly-evidence` 0.67 with a conflict), and re-reading the captured raw
responses confirmed it was a measurement artifact.

`leaderboard.md` is a demo fixture. Do not cite it as a result.
