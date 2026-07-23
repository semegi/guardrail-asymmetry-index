# Guardrail Asymmetry Index — Leaderboard

Higher GAI = performs more of the defensive job (less guardrail lockout).
`attacker_gap` = distance from a no-refusal attacker. `jailbreak_delta` > 0
means the capability is present but a guardrail suppressed it.

| Model | GAI | Attacker gap | Jailbreak delta | Costly-evidence | Suppressed (conflicts) |
|-------|-----|--------------|-----------------|-----------------|------------------------|
| open-weight-local | 0.75 | 0.25 | +0.25 | 0.67 | 1 |
| guardrailed-frontier | 0.00 | 1.00 | +1.00 | 0.00 | 3 |
