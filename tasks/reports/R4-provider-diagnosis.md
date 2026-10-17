# Worker report: R4 — provider HTTP 400 diagnosis

**Worker/model/effort:** timeout_fix; model metadata unavailable
**Status:** complete-for-review
**Interface revision:** shared v1 contract; R3 final-synthesis change

## Delivered

All nine E4 provider errors have the same safe HTTP 400 message. Saved evaluation metadata records **six successful served-model calls before each failure** (Q2, Q3, Q8-1/-2, Q9-3/-4/-6, Q10, Q11). R3 enables tools only for loop rounds 0–5, then makes final synthesis calls with `tools=[]`; `CompatibleProvider` serializes that as `"tools": []`. This made a failure on first tool-free synthesis a strong, consistent hypothesis, though the captured run alone did not prove it. The failure bodies were intentionally not persisted.

Implemented the bounded compatibility fix: final synthesis and its one repair now retain the complete tool definitions for the preceding assistant tool-call history while sending `tool_choice:"none"`. The first six tool-enabled rounds keep the previous default tool choice and behavior. DigitalOcean's official Agent Inference Chat Completions schema shows `tool_choice:"none"` alongside a nonempty `tools` array; the [OpenAI Chat Completions reference](https://platform.openai.com/docs/api-reference/chat/object) defines `none` as preventing tool calls. The configured endpoint is DigitalOcean, so its primary API schema is the relevant compatibility evidence.

The context failures are a separate issue. Ten E4 turns hit the existing 96,000-character history cap; error calls show 75,983–120,710 prompt tokens where usage was saved. Do not infer that raising wall-clock budgets fixes this. Context reduction/compaction needs separate, contract-aware work; blindly raising the cap risks oversized requests.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| Read E4 report and aggregate saved per-turn metadata | pass | `tasks/reports/E4-final-rerun.md`; each of nine 502 responses records six served-model IDs and safe HTTP 400 only |
| Read-only comparison of R3 loop/provider payload | pass | `app/agent.py` gates tools after six rounds; `app/provider.py` sends the passed `tools` value. No raw failed request/body is persisted. |
| `python3 -m pytest -q tests/test_provider.py tests/test_agent.py` | pass | 61 passed in 13.59s; fake transport checks `tools` is retained with `tool_choice:"none"`, and the agent uses that mode only for final synthesis/repair. |
| Paid provider calls | not run | Prohibited by assignment. |

## Limits and decisions needed

This fix addresses the request-shape compatibility hypothesis, not a proven root cause. The captured E4 report remains an unchanged record of the prior run; confirm with a fresh run only if separately authorized. The context failures are separate: ten E4 partials hit the 96,000-character history cap; error calls show 75,983–120,710 prompt tokens where usage was saved. Do not infer that larger wall-clock budgets fix context exhaustion or raise the context cap blindly.

## Handoff

Changed only the assigned provider, agent, focused tests and this report. Sol can review and decide whether to restart the live worker; this change has not been verified against paid inference. Safe error reporting remains intact and no retries were added.

**Sol review:** accepted as a bounded compatibility repair; root61 focused tests pass. Backend restarted after confirming no pending live requests. No paid post-R4 inference check; the E4 evaluation remains the pre-R4 result.
