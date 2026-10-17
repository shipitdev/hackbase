# Context-pipeline final evaluation

**Run:** `scripts/evaluate_context_pipeline.py --run`
**Dataset:** `dataset-7207fefc8284` · **Analysis date:** 2027-01-15
**Scope:** 21 released turns, official order, one attempt per turn, isolated knowledge and private-memory databases.

## Results

- 21/21 turns attempted; 13 HTTP 200 responses marked `partial`; 8 HTTP 502 responses without an answer; no HTTP 504.
- No final response reported an application context-limit error. The earlier E4 run had ten context-limited partial responses.
- Of the eight provider failures, five reported an invalid response format, two reported that the requested model was unavailable for the account tier (HTTP 403), and one reported rate/credit limiting (HTTP 429).
- Seven HTTP 200 responses ended in answer-schema or citation validation errors; one ended in SQL repair failure.
- Q1's refusal to invent reservoir pressure and Q9-2's Northwest Production lead/count were independently source-checked. Q8-3 and Q9-1 returned recall results tied to saved query rows, but were not independently scored against a separate oracle.
- No broad accuracy percentage is claimed. The saved run reports 1,988,031 tokens; failed calls may omit usage, so this is a lower bound.

The run shows fewer explicit context-limit failures than E4, while answer validation and upstream provider failures remain. All captures, raw conversations, result rows and isolated databases are under ignored `data/evaluations/context-pipeline-final/`; they are not included in this public report. The active demo databases were not changed.

See [the two-section write-up](writeup.md) for each turn's observed output and verdict, and [E4](../tasks/reports/E4-final-rerun.md) for the earlier run.
