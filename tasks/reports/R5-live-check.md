# R5 — targeted Q4 context-fix live check

**Status:** completed one authorized attempt; failed the answer acceptance gate after validation repair. No retry.

## Scope

Run only the existing exact Q4 check in `scripts/check_timeout_fix.py`, owned by Chris Dalton (`U-402`), with its required table instruction. Reuse the helper with `CHECKS = [original_CHECKS[1]]` and `OUT = data/evaluations/context-fix`. This is one fresh isolated source snapshot and memory database, with one write-ahead attempt fence and no automatic retries. Earlier E3/R2/R3 output remains unchanged.

## Preparation

| Check | Outcome |
|---|---|
| `python3 -m py_compile scripts/check_timeout_fix.py` | Pass |
| Helper preflight and isolated snapshot initialization | Pass before dispatch; Q4/U-402 only; final dataset `dataset-7207fefc8284`, analysis date `2027-01-15`; write-ahead fence recorded before the single attempt |
| Private path permissions | Pass; output directory `0700`, snapshot and memory DB `0600` |
| Paid call | One authorized attempt; 180.653 seconds; HTTP 200 `partial`; answer gate failed (details below) |

The private state, isolated DBs and one-shot result are under ignored `data/evaluations/context-fix/Q4/`. The live database and memory were not changed.

## Source oracle for review

Compare any returned answer with `tasks/reports/E4-source-oracles.md` and the private `data/evaluations/source-oracles/oracle.json`. Expected Q4 evidence includes current bypass `0248` (allowed), `0249` (expired) and `0405` (not approved), plus violations `0087`, `0158`, `0249`, `0405` and `0561`. The requested output must be an actual table with the requested fields and supporting citations/saved rows. HTTP success alone is not a pass. If the result fails validation or provider execution, retain its safe reason and private trace without replaying.

## Live result

One Q4 request was dispatched as Chris Dalton (`U-402`), request `timeout-fix-Q4`, on a fresh thread and isolated snapshot. It completed in 180.653 seconds with HTTP 200 and `status: partial`. The safe answer says: “I couldn't verify the answer: The final answer failed validation after its one repair: Draft was not valid JSON.” There was no rendered UI, answer table, citation list, or returned results in the final response. This is an answer-validation failure, not a timeout or a semantic pass.

The response reports 8 served model calls and 134,706 total recorded usage tokens (121,301 prompt; 13,405 completion). The 90-second provider and 240-second overall budgets were not exceeded. There was no HTTP 502/504 or context-limit message; this trial ended on final-answer JSON validation. Exact peak prompt-context length was not captured, so it is unknown. No paid retry was made.

The private memory trace contains 14 tool traces: four successful saved SQL results, document/evidence lookups, one rejected query using unauthorized `GROUP_CONCAT`, and two final `answer_validation` attempts, both rejected with `Draft was not valid JSON.` Several saved note rows include the five oracle violation wells (`0087`, `0158`, `0249`, `0405`, `0561`) and current candidate `0248`; however, the final response provided no synthesized approval intervals/statuses and no cited table. I therefore do not credit any of the six unique target wells as answered. The oracle requires three current statuses (`0248` allowed, `0249` expired, `0405` not approved) plus five violation intervals (`0087`, `0158`, `0249`, `0405`, `0561`); this trial did not produce a reviewable answer against those values.

Full prompt/response/state and saved query rows are preserved in private `result.json`, `state.json`, and `results.json`. The private trace is `traces.json`; its folder/files are mode-restricted. The sole transport result and failure reason are captured. No timeout inference or accuracy claim is made from HTTP 200.

**Sol review:** accepted as a completed targeted run, not a passing answer. No context-limit or timeout was returned; peak prompt size was not recorded. Final JSON failure remains unresolved. No further paid calls authorized for this submission sprint.
