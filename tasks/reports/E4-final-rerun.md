# Released questions — final rerun

**Dataset:** `dataset-7207fefc8284` · 600 assets · analysis date 2027-01-15  
**Run:** 21 turns in official order, one attempt per turn, fresh isolated snapshot and persistent private memory under `data/evaluations/final-rerun/`. No E3/R2/R3 artifacts or active databases were changed.

## Outcome

Only two turns returned useful, source-supported answers: Q1 correctly refused a reservoir-pressure map because the records contain no pressure measurements; Q9-2 correctly named Nathan Pierce and 150 wells, with four saved-query citations. The other 19 turns did not yield verifiable answers.

There were 12 HTTP 200 `partial` responses and nine HTTP 502 provider errors. Ten partial answers stopped at the 96,000-character context limit; Q1 and Q9-2 are the two useful responses. All nine 502s safely reported an upstream HTTP 400. No HTTP 504 occurred. The active timeout settings were `LLM_CALL_TIMEOUT_SECONDS=90` and `ANSWER_TIMEOUT_SECONDS=240`; the web proxy's 300-second limit was not exercised by this in-process check. The observed bottlenecks were context growth and upstream HTTP 400 responses, not request timeout.

Recorded usage is a lower bound: 1,705,355 prompt tokens, 35,025 completion tokens, 1,740,380 total tokens across 103 served-model IDs (12 `kimi-k3`, 91 `qwen3.8-max`). Some failed final provider calls may not report their own usage. Total measured turn time was 707.951 seconds. Each error and partial was preserved; no paid call was retried.

## Scenario results

| Scenario | Returned output and evidence verdict |
|---|---|
| **Q1 — Reservoir pressure** | **Supported refusal.** It explains the absence of pressure measurements, cites a scan of 125,198 inspections with zero pressure matches and the equipment inventory, and correctly produces no map. |
| **Q2 — Best producer** | **Failed; answer unverifiable.** Provider HTTP 400; no answer. Source oracle confirms there are no per-well oil-volume measurements, so the proper result is a refusal to rank barrels. |
| **Q3 — Gas reports** | **Failed; answer unverifiable.** Provider HTTP 400; no table. The oracle expects 26 qualifying reports: 17 responses met the SOP deadline and 9 missed. |
| **Q4 — Flowline bypasses** | **Partial; unverifiable.** Context-limit partial; no table, citations or results. The oracle has 12 bypass intervals, 3 current, and 5 violations. |
| **Q5 — Regulator letter** | **Partial; unverifiable.** Context-limit partial; no table or evidence to compare with the regulator letter. |
| **Q6 — Status disagreements** | **Partial; unverifiable.** Context-limit partial; no table or evidence. |
| **Q7 — Repair priorities** | **Partial; unverifiable.** Both turns reached the context limit; no ranked table or crew recommendation. The oracle does not assert a unique ranking. |
| **Q8 — Recall and memory** | **Mixed failure; no answer verified.** Turns 1–2 returned provider HTTP 400; turns 3–5 reached the context limit, with no recall tables or sourced facts. No shared changes were accepted (evaluation DB remained at revision 1), so cross-session persistence was not demonstrated in this run. |
| **Q9 — Multi-topic session** | **Mixed.** Turn 1 context-limited. **Turn 2 supported:** named Nathan Pierce and 150 TEAM-NW wells, supported by four saved-query citations and the source roster. Turns 3, 4 and 6 returned provider HTTP 400; turn 5 reached the context limit. For turn 4, the source oracle says there is no Dec 3 H2S reading; the latest documented earlier reading is 0 ppm on Nov 20. The model supplied no answer, so no contemporaneous value was invented. |
| **Q10 — Waiting on work** | **Failed; answer unverifiable.** Provider HTTP 400; no table or stacked bar. |
| **Q11 — Hotter region** | **Failed; answer unverifiable.** Provider HTTP 400; no evidence or comparison. |

The independent oracle in `tasks/reports/E4-source-oracles.md` supplies the Q3/Q4 counts and the Q9-4 evidence boundary. No numerical accuracy percentage is claimed: only Q1 and Q9-2 returned answers suitable for evidence checking. For Q9-2, TEAM-NW's stored lead is U-601, the user record resolves that ID to Nathan Pierce, and the current team roster contains 150 wells.

## Reproduction and limits

Run used the existing `scripts/evaluate_final.py` imported with `OUT` redirected to `data/evaluations/final-rerun`, then `main()`; its scenario prompts/order were unchanged. The private directory contains all 21 full prompts, responses, UI specs, returned results, errors, per-turn model/usage/latency data, shared evaluation DB, memory DB and attempt state. The output is mode-restricted and ignored by Git. This report contains paraphrased outcomes rather than runtime chat transcripts.

**Sol review:** accepted as the complete post-fix run, not a successful product evaluation. All21 captures were exported to the local submission bundle. Only two turns have supported key conclusions; HTTP200 counts are not an accuracy score. No timeout elimination beyond the observed run is guaranteed.
