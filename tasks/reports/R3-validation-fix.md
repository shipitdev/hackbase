# Worker report: R3 — final-answer validation recovery

**Worker/model/effort:** GPT-6 Codex worker; runtime model/effort unavailable
**Status:** complete-for-review
**Interface revision:** Native OpenUI v2 / current backend contracts

## Delivered

The final two of eight model rounds now require synthesis without tools, leaving one round for a final repair. Tool-batch repair and final-answer repair have separate one-attempt counters. Repeated draft failures return a bounded safe reason and record that same reason in the private trace; schema diagnostics list only known draft field names. Unverified answers still fail closed under the existing citation, evidence, ownership, and OpenUI validation.

E3 and the captured R2 Q9-2/Q4 turns retain no rejected model drafts or validation exceptions, so the exact failed field cannot be recovered. Both R2 partials occurred before eight calls (Q9-2: five provider calls/four tool traces; Q4: seven calls/seven tool traces). This supports a repair-path issue but does not prove which validation failed. The change addresses both early repair exhaustion and runs that consumed tool rounds without final synthesis.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest -q tests/test_provider.py tests/test_agent.py` | pass | 60 passed in 12.72s; fake provider cases cover final-round tool suppression, independent repair allowances, and safe validation diagnostics. |
| `git diff --check -- app/agent.py tests/test_agent.py` | pass | No whitespace errors. |
| Private E3/R2 trace metadata inspection | pass | Read-only; no private conversation text or raw model drafts printed. |

## Limits and decisions needed

Tool-enabled rounds are capped at six to reserve two synthesis rounds, with up to eight calls per batch. A model that still fails final validation after the repair returns a partial answer with the safe reason. No live provider calls were made.

## Handoff

Released `app/agent.py`, `tests/test_agent.py`, and this report for review. R2 private artifacts and active data/memory databases were not modified.

**Sol review:** accepted as bounded recovery/diagnostics change. Root reviewed the new branches, reran60 focused tests (pass), restarted backendPID36226, and authorized one fresh Q9-2 check. Live answer success remains pending.
