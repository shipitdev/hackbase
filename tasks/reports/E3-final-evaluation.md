# Worker report: E3 — released final evaluation

**Worker/model/effort:** GPT-6 Codex worker; model and effort reported by runtime: unavailable
**Status:** complete-for-review
**Interface revision:** native OpenUI v2, six-view contract

## Delivered

Added `scripts/evaluate_final.py` for the 11 released questions in order (21 turns), including the full table/chart directions, named user IDs, owner-qualified sessions, and analysis date 2027-01-15. It uses one private snapshot of the activated knowledge DB and a fresh private evaluation memory DB shared across users and sessions. Each turn is write-ahead recorded and attempted once; ambiguous attempts are never automatically replayed. Per-turn files keep the full response, UI, returned result data, errors, and available model/usage/latency metadata under ignored `data/evaluations/final-release/`.

Activation snapshot: dataset version `dataset-7207fefc8284`, initial knowledge revision 1, 600 assets, 125,198 inspections, and 17,415 maintenance records. The final isolated DB advanced to revision 2 after the Q8-4 shared claim. The active knowledge and private memory databases were not modified.

## Run and aggregate outcome

| Command | Outcome |
|---|---|
| `python3 -m py_compile scripts/evaluate_final.py` | Pass |
| `python3 -c "import runpy; runpy.run_path('scripts/evaluate_final.py', run_name='evaluation_preflight')"` | Pass; embedded assertions check 11 ordered scenarios, 21 turns, Q3 columns, Q8 source directions, Q9 shared thread, and Q10 stacked-bar direction |
| Initial `python3 -u scripts/evaluate_final.py --run` | Stopped before dispatch; `ModuleNotFoundError: app`. No provider request was made. |
| `python3 -u scripts/evaluate_final.py --resume` | Completed after adding the project root to `sys.path`; captured 21/21 turns. |

The run ended with 16 HTTP 200 responses, all carrying `status: partial`, and five HTTP 504 provider timeouts. No turn returned `status: complete`. Captured metadata records 97 served-model IDs (41 `kimi-k3`, 56 `qwen3.8-max`) and a usage lower bound of 1,590,848 prompt tokens, 51,451 completion tokens, and 1,642,299 total tokens. Some timed-out calls have no usage metadata, so actual billed usage may be higher. No paid request was retried.

## Semantic review against released sources

| Question | Captured result and evidence verdict |
|---|---|
| Q1 — reservoir pressure | Validation-budget partial; no answer, citation, result or map. The released inspection schema has temperatures and spill fields, with no reservoir-pressure measure. A refusal would be supported by the data, but the model did not provide one; this is a failure. |
| Q2 — best producer | Partial answer with seven citations and a saved 10-row result. It correctly says barrels per well are not measured and cites the manuals’ rule against inferring production volume from temperature. Its 52-well tie at 53/53 producing inspections is a clearly labeled proxy, not an answer to oil volume. Verdict: safe, evidence-supported refusal with a useful but unsolicited proxy. |
| Q3 — gas response deadlines | Validation-budget partial; no response table or citations. The applicable timing rules are in the released operating SOP, but the answer did not evaluate any report. |
| Q4 — temporary bypasses | HTTP 504 timeout; no answer or visual. |
| Q5 — regulator letter/spills | Context-budget partial; no table or citations. Not assessable. |
| Q6 — inspection/note disagreement | Context-budget partial; no table or citations. Not assessable. |
| Q7 — repair risk | Turn 1 HTTP 504; turn 2 partial because the context budget was reached. No ranking, crew recommendation, table or source citations. |
| Q8 — recall and memory | Turns 1–2 HTTP 504; turns 3 and 5 context-budget partial; turn 4 validation-budget partial. No requested recall table or fact-by-fact sourcing. Turn 4 nevertheless persisted an accepted shared claim about WELL-0577. The released supplier notice recalls lot `LOT-2409-A`; report `MNT-0577-028` says that lot was installed on 31 Jul 2026, before the 1 Dec notice, and the released maintenance history has no later downhole-pump replacement. The claim does not remove the pump via an override, but its explanation omits the installed recalled lot and is unsafe to treat as proof the pump was removed. Q8's downstream recall checks were incomplete, so cross-session behavior was not demonstrated in the returned answers. |
| Q9 — multi-topic session | Turns 1, 4–6 were partial due context/validation budgets; turn 3 timed out. Turn 2 correctly named Nathan Pierce as Northwest Production lead and reported 150 wells. Four citations and saved query results support the lead and count; verdict: supported answer with an explicit data-currentness limitation. |
| Q10 — waiting on parts/crews/etc. | Context-budget partial; no table or chart. Stacked-bar behavior was not exercised. |
| Q11 — hotter region | Validation-budget partial; no answer, evidence or result. Not assessable. |

The source supports a refusal for Q1 because pressure is unmeasured, and Q2 because per-well oil volume is unmeasured. Only Q2 returned that refusal with evidence. Q1 is counted as an execution failure, not as a successful refusal. Aside from Q2 and Q9-2, the final answer payloads did not provide evidence sufficient for factual assessment.

## Limits and handoff

Full private responses, UI specs, results, errors, and per-turn metadata remain in `data/evaluations/final-release/Q*/` with state and isolated databases alongside them. Review individual records there without publishing runtime conversation text. The observed main limitation is model context/validation exhaustion on complex released questions, with provider timeouts on five turns. Source assessment is definitive only for the two fact-bearing answers and the WELL-0577 memory side effect; other scenario correctness remains unknown because no verifiable answers were returned. Sol review: accepted as a completed evaluation run, not successful product acceptance. Root verified all21 recorded turns (16HTTP200/5HTTP504), independently confirmed Nathan Pierce and150 Northwest wells, and confirmed the active database remains revision1 with zero shared changes. Q2 refusal is supported; its proxy is not oil-volume accuracy. No broad pass rate is justified.
