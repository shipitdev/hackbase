# Worker report: R2 — configurable time budgets

**Worker/model/effort:** GPT-6 Codex worker; runtime model/effort unavailable
**Status:** complete-for-review
**Interface revision:** Native OpenUI v2 / current backend contracts

## Delivered

Added validated finite-positive `LLM_CALL_TIMEOUT_SECONDS` and `ANSWER_TIMEOUT_SECONDS`; absent settings retain the 45-second provider and 120-second answer-loop budgets. Each provider call is capped at the lesser of its configured timeout and the remaining answer budget. Invalid settings fail with a safe configuration error. No retries, model changes, context-cap changes, or prompt redesign were added.

E3 records five provider 504s: three at about 45 seconds, one at about 78 seconds, and one at about 120 seconds. Separate 96,000-character partials are context exhaustion, not provider timeouts. The no-history base prompt measured 37,573 characters against the 96,000-character cap; source rules account for 26,176, so the initial rulebook is not already over budget. Longer budgets cannot resolve later history/result growth.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest -q tests/test_provider.py tests/test_agent.py` | pass | 56 passed in 12.11s; fake transport/provider cover configuration, validation, preserved defaults and remaining-budget clamping. |
| E3 metadata and base-prompt length inspection | pass | Read only per-turn status/timing/error summaries; no runtime conversation text printed. |

## Limits and decisions needed

Recommend `LLM_CALL_TIMEOUT_SECONDS=90` and `ANSWER_TIMEOUT_SECONDS=240` for the next orchestrator-controlled run. HTTPX applies its timeout to connection/read operations, so a response that streams slowly can exceed that duration in wall time; the total answer budget is also checked between calls/tools. Provider or hosting-side limits can still return 504. Context remains capped at 96,000 characters.

## Handoff

Released `app/provider.py`, `app/agent.py`, `tests/test_provider.py`, `tests/test_agent.py`, and this report for review. No live provider calls or environment changes were made.

**Sol review:** accepted. Root reran56 focused tests (pass), set ignored.env90/240seconds, restarted backendPID35450 and verified health through the frontend proxy. Root found frontend Vite proxy150s shorter than the new answer budget and raised it to300s; Vite reloaded its configuration. Live two-question validation is delegated separately; no claim all timeouts are eliminated.
