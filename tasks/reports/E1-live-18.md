# E1 live backend evaluation — 17 October 2026

**Worker/model/effort:** GPT-6 Luna high (assigned)
**Status:** partial
**Interface revision:** OpenUI v2; only ResultCard and ResultTable are registered

The 18 official questions were run in isolated SQLite snapshots with the configured DigitalOcean inference-router. The harness made one provider attempt per live turn; independent scenarios continued after errors. It saved 29 required turns: 19 returned HTTP 200 partial answers, 8 returned errors (including the interrupted Q12 repeat), and 2 dependent turns were blocked. Q15 Laura’s first request was rejected before provider use because it reused Jessica’s thread; that evidence is saved separately. A corrected, user-owned thread then made the only provider attempt for that turn and timed out.

| Q | Data or memory outcome | Requested visual / limitation |
|---|---|---|
| 1 | Correct latest inspection, 3.2°C delta, not-producing status and planned shut-in; partial with no live telemetry caveat. | Status card returned. |
| 2 | Four stopped wells and deltas match saved rows; reasons are cautious where unknown. | Table returned. |
| 3 | 13 readings and stopped markers returned in a table. | Line chart unsupported; table fallback stated. |
| 4 | Six spills, 15.1 bbl; six source rows exclude the corrected false positive. | Summary card and table returned. |
| 5 | 21 days from three inspections; response also includes repair-hour context. | Card and table returned. |
| 6 | Validation budget exhausted; no verified well ranking. | Bar chart absent; unsupported. |
| 7 | Validation budget exhausted; no verified spill list. | Map absent; unsupported. |
| 8 | Area totals match; saved grid has 38 of 40 area-month cells, omitting explicit zero rows. | Heatmap unsupported; table fallback, zero cells missing. |
| 9 | Provider 502: “too many simultaneous tools”; no answer. | No table. |
| 10 | Validation budget exhausted; no verified spill rows. | Requested table absent. |
| 11 | Validation budget exhausted; costs and prior well list not returned. | No visual requested. |
| 12 | Standalone correction timed out; follow-up repeat request was interrupted without a response and new-chat check blocked. The same temperature correction was accepted in the isolated Q15 scenario. | Q2 table repeat not verified. |
| 13 | Standalone response timed out, but the 5.4 bbl correction was accepted in its snapshot and again in Q15; regulatory explanation was not returned. | No visual requested. |
| 14 | Michael’s T350 pump-jack RCA threshold of two was accepted with the requested scope. Baseline and new-chat lists exhausted validation budget. | Table checks not returned. |
| 15 | Both corrections were accepted; Jessica saw WELL-0164 producing and the conflicting note. Laura’s turn timed out. | Laura’s spill table not returned. |
| 16 | Jake’s planned-workover claim was accepted, but the response timed out; Michael’s dependent check was blocked. Jessica’s private-history turn returned only a validation-budget limitation. | No visual requested. |
| 17 | Michael’s WELL-0175 claim was accepted; Tyler’s and Jake’s follow-ups timed out, so disagreement handling remains unverified. | No visual requested. |
| 18 | “Yes” and both evidence notes were returned, but both conflict entries were marked resolved and the answer treated the HSE note as definitive; expected behavior preserves the note-level disagreement. | No visual requested. |

The four visuals beyond the registered Card/Table set were not delivered: Q3 line chart (table fallback), Q6 bar chart (no answer), Q7 map (no answer), Q8 heatmap (table fallback). No browser or Playwright check was run.

## Checks and usage

| Command or check | Outcome | Evidence |
|---|---|---|
| `python3 -m py_compile scripts/evaluate_questions.py` | Pass | Harness syntax check. |
| `python3 -u scripts/evaluate_questions.py --resume` | Completed with recorded partials/errors | 29 per-turn outcomes and isolated snapshots under `data/evaluations/e1/`; one final invocation repaired the pre-provider Laura thread ownership issue. |
| Result/correction inspection | Partial | Saved results and isolated `changes` tables inspected; no production databases were modified. |

Completed answer payloads report 102 served-model entries (`kimi-k3`, `glm-5.3-flash`) and 1,238,875 prompt tokens plus 52,755 completion tokens (1,291,630 total). Timed-out/error turns did not return usage, so these are lower bounds; no dollar cost is inferred. Raw answers, user chats and SQLite snapshots are private, mode 0600, and under the ignored runtime directory.

**Limits and decisions needed:** Four requested visual types are not implemented in the current UI. Provider timeouts and tool-budget failures left several numeric, memory and dispute checks unverified. No automatic paid retries were made.

**Handoff:** Luna’s assigned files are ready for Sol review. Reproduction/resume command: `python3 -u scripts/evaluate_questions.py --resume`. Sol review pending.

## Sol review note

Reviewed without rerunning live tests. These are partial/error outcomes, not an18/18 success. The [reviewed per-question results](E1-reviewed-results.md) correct the Q18 overstatement: its yes conclusion and both sources match the official expectation; resolution wording remains a semantics review. The original run also had timestamp/dependency/thread weaknesses, and shared writes may have persisted despite HTTP failure. Original runtime artifacts remain unchanged. See E2-evaluation-review.md and R1-runtime-reliability.md for subsequent offline-only harness and runtime repairs.
