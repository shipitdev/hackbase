# Updated context-pipeline evaluation status

**Snapshot:** 17 October 2026, 18:31 India time
**Evaluation:** `scripts/evaluate_context_pipeline.py --run`
**Dataset:** `dataset-7207fefc8284`; 21 released turns; isolated evaluation databases under the gitignored `data/evaluations/context-pipeline-final/`.

At this snapshot, 16 of 21 turns had been attempted: 11 returned HTTP 200 `partial`, 4 returned HTTP 502 without an answer, and 1 request was still pending. No correctness verdict has been assigned to these new responses. An HTTP 200 or a saved partial response does not mean the answer is correct. At least one captured response still referred to a context limit. The run was active when this status was recorded, so these counts are a time-specific snapshot, not final totals.

For comparison, the previous completed full run (E4) captured all 21 turns: 12 HTTP 200 partial responses and 9 HTTP 502 errors; only Q1 and Q9-2 were judged source-supported. That is 2/21 verified answer coverage, not a general accuracy score. E4 predates the context-preview and compaction changes. Its detailed results are in `tasks/reports/E4-final-rerun.md` and the two-page write-up.

The new run's early provider-error count (2 of 12 attempted) is lower than E4's 9 of 21, but the runs are incomplete at different stages and the newly captured answers have not been reviewed against source records. Do not interpret this as an accuracy improvement. Final comparison requires the completed 21-turn capture and evidence review.
