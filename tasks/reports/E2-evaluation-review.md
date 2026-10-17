# E2 — offline evaluation harness review

**Worker/model/effort:** evaluation-review worker; exact runtime model/effort not exposed
**Status:** complete-for-review
**Interface revision:** OpenUI v2

## Delivered

Repaired the evaluator’s replay fence and outcome labels, made ambiguous interrupted requests require manual review, and gated dependent turns on confirmed persisted setup. A shared write can satisfy its dependency after a timeout only when the isolated database confirms it; Q6’s saved memory list must match the expected three wells exactly. New snapshots record source/snapshot hashes and dataset revision, user-qualified thread keys, ordered per-turn timestamps, and restore the memory clock after each step. The clock advances by a microsecond per storage timestamp, preserving user-before-assistant order. Error `evaluation_metadata` is captured through an allowlist. Historical E1 outcomes and databases were not changed. The reviewed 18-question verdict table is [E1-reviewed-results.md](E1-reviewed-results.md).

Read-only inspection found the Q12, Q13, Q14, Q16 and Q17 shared writes persisted in their isolated databases despite response timeouts or validation-limited answers. The verdict artifact separates those writes from unverified downstream answers. Q18’s yes conclusion and both note sources align with the official expectation; the `resolved` conflict labels remain a manual semantics review. Recommended policy: preserve note-level disagreement separately from the observed spill conclusion.

## Checks

| Command or check | Outcome | Evidence / exact failure |
|---|---|---|
| `pytest -q tests/test_evaluate_questions.py` | Pass | 11 offline tests; fake provider/store with real `TestClient` and `MemoryStore`, including ordered unique user/assistant timestamps and clock restoration. Additional fake-client cases cover replay fencing, error metadata, persisted dependencies and exact Q6 setup. |
| `python3 -m py_compile scripts/evaluate_questions.py tests/test_evaluate_questions.py` | Pass | Both assigned Python files compile. |
| E1 runtime rerun | Not run | Explicitly out of scope; no live provider calls made. |

## Limits and decisions needed

The historical E1 run did not record source database hashes or durable per-tool checkpoints, so exact original-vs-active baseline provenance cannot be reconstructed from its state files. The ignored Q12/Q13/Q16 databases do confirm accepted writes; their dependent answers remain unverified. Q18 policy recommendation is for Sol’s review; no app or shared contract files changed.

## Handoff

Assigned files are ready for review. E1 runtime snapshots and original outcomes remain untouched; the main checklist stays with Sol.

**Sol review:** accepted after two concrete runner regressions were repaired and covered by worker-run offline tests. Historical E1 is evidence with limitations, not full evaluation acceptance.
