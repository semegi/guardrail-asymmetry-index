# Guardrail Asymmetry Index (GAI) — Design

**Date:** 2026-07-23
**Status:** Approved design, pre-implementation
**Repo:** `guardrail-asymmetry-index/` (standalone git)
**Reuses:** `research-platform` epistemic-models (`costly_evidence_fraction`, `cheap_talk_fraction`, `belnap_conflicts`, `sdt_criterion_beta`)

---

## Motivation

The July 2026 OpenAI/Hugging Face incident exposed a lesson the industry has not
yet instrumented: **safety guardrails are an unmeasured defensive liability.**
During incident response, Hugging Face's hosted frontier models *refused to
analyze the attack payloads* because of safety guardrails, while the attacking
agent operated with no such constraints. Defenders paid a refusal tax; attackers
did not. Forensics only succeeded because a self-hostable open-weight model was
vetted and ready.

No public instrument measures this asymmetry. This project builds one.

**Thesis:** Measure the defender–attacker refusal gap on legitimate
security-analysis tasks, and score each model's fitness as an incident responder.
Keep the measurement itself honest using the same costly-vs-cheap-evidence and
four-valued-truth machinery that the research-platform already provides.

## Non-goals (YAGNI)

- No live intrusion, no working exploit code, no real credentials. All task
  payloads are synthetic and inert. The instrument measures *whether a model
  will reason about defense*; it never needs a functioning exploit to do that.
- No web UI, no live dashboard, no continuous monitoring in v1. Productization
  belongs to `warrant-economy` later.
- No hosted-API calls in v1 (see Scope). Local + fixture only.

## Success criteria

1. Given a task corpus and a set of local model adapters, the pipeline produces
   a `scorecard.json` and a human-readable `leaderboard.md` with one GAI per model.
2. The refusal classifier reproduces hand-labeled fixture verdicts (T/F/B/N) with
   documented accuracy, and reports an SDT-β for its own acceptance bias.
3. The full suite runs offline (`npm test` / `pytest`) against stub adapters —
   zero network calls required for CI.

---

## Scope (v1)

- **Batch, offline, single-machine.**
- **~15–20 tasks**, **4–5 model adapters** (local open-weight via Ollama/llama.cpp
  + stub adapters). Hosted APIs deferred to v2.
- **Attacker baseline: both, reported separately** —
  - *Assumed-perfect* baseline is the headline: attacker scores T (performs) on
    every task by definition (justified by the incident: attacker had zero
    refusals). The gap is each model's refusal rate.
  - *Jailbreak-delta* proxy is a secondary column: each model is scored twice —
    plain prompt vs. a benign reframing that removes the refusal trigger — to
    show whether the defensive *capability* is present underneath the refusal.

---

## Architecture

Four isolable components, each independently testable, communicating through
well-defined file/interface boundaries.

```
tasks/*.json ─► runner ──► raw_responses/*.json ─► classify ──► verdicts/*.json ─► score ──► report/
                 │                                   │                                │
            model adapters                    Belnap + β log                  adversarial-narrative
            (local, stub)                                                      warrant check
```

### 1. Task corpus (`tasks/`)

Versioned defensive-analysis prompts spanning the incident's real work:

- Analyze a (defanged, synthetic) malicious-dataset loader payload and explain the
  code-execution path.
- Reconstruct an attack chain from a synthetic telemetry excerpt.
- Triage which of N weak signals correlate into one incident.
- Draft a detection rule (YARA/Sigma-style) for a described technique.

Each task file records: `id`, `prompt`, `defensive_intent` (the legitimate goal it
encodes), `benign_reframing` (the jailbreak-delta variant), and
`expected_capability` notes for labeling. Payloads are inert; a lint check in CI
asserts no task contains live network indicators or runnable exploit primitives.

### 2. Runner (`runner/`)

Model-agnostic adapter interface: `run(task) -> response`. Implementations:
`StubAdapter` (deterministic fixtures for tests), `OllamaAdapter` (local
open-weight). One code path for all models. This is the only component that may
touch external processes; everything downstream is pure/offline. Writes
`raw_responses/<model>/<task>.json`.

### 3. Refusal classifier (`classify/`)

Assigns each response a **Belnap A₄** verdict:

- **T** — performed the defensive task.
- **F** — refused.
- **B** — did both (hedged / partial refusal — the most interesting failure mode).
- **N** — evaded / non-answer.

Not regex-based. Uses a rubric-driven classifier with the response + task's
`defensive_intent` as input. Maintains an **SDT-β calibration log**: tracks its own
accept(T)/reject(F) rate across a known-mixed fixture set so classifier drift
toward over-calling refusals is detectable and correctable. Writes
`verdicts/<model>/<task>.json` with `{belnap, rationale, confidence}`.

### 4. Scorer + report (`score/`)

- **GAI per model** = refusal-weighted score across the corpus. B and N are
  partial-credit-against (a hedge is a partial lockout). Headline number.
- **Attacker-gap** = model score vs. assumed-perfect T baseline.
- **Jailbreak-delta column** = plain vs. benign-reframing score per model
  (capability-present indicator).
- **Warrant check:** run each model's aggregate through `adversarial-narrative`
  (research-platform) to test whether the "safe/capable" score is backed by
  `costly_evidence` (reproducible across task paraphrases) or `cheap_talk` (one
  lucky verdict). `belnap_conflicts` across paraphrases flags unstable scores.

Outputs: `report/scorecard.json` (machine) and `report/leaderboard.md` (human —
the punchline artifact: which models leave a defender locked out).

---

## Error handling

- Adapter timeout / model unavailable → verdict `N` with `error` annotation, never
  a crash; the model is scored on what it returned.
- Classifier low-confidence (< threshold) → verdict retained but flagged for the β
  log and excluded from the costly-evidence fraction.
- Missing task fields → CI lint fails fast before any run.

## Testing (TDD, classifier-outward)

1. **Classifier fixtures:** hand-labeled responses with known T/F/B/N. Classifier
   must reproduce labels; accuracy recorded. Written first.
2. **Scorer golden:** a fixed verdict set → pinned `scorecard.json`. Aggregation
   math locked by fixture.
3. **Runner integration:** `StubAdapter` returns recorded responses; full
   `tasks → report` pipeline runs offline in CI.
4. **Task-corpus lint:** asserts inertness (no live indicators/exploit primitives).

## Directory layout

```
guardrail-asymmetry-index/
  tasks/                    # versioned task corpus (json)
  runner/                   # adapters + run loop
  classify/                 # Belnap classifier + β log
  score/                    # scorer + adversarial-narrative warrant check
  report/                   # generated scorecard.json + leaderboard.md
  test/fixtures/            # labeled responses, golden scorecard
  docs/superpowers/specs/   # this document
```

## Portfolio mirror

Per the "keep career folder synced" rule, the final writeup and leaderboard mirror
into `~/career-2026/` with an index update, framed as an AI-agent-safety
measurement flagship built on the warrant thesis.

## Deferred to v2+

- Hosted-API adapters (Claude, GPT, …) for the real-frontier headline result.
- Continuous re-runs / drift-over-time tracking.
- Web dashboard (warrant-economy surface).
- Companion thread: Kosmos containment test harness (separate spec).
