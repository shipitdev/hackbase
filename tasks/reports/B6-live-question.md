# B6 — live backend Q1 question check

**Worker/model/effort:** GPT-6 Luna / high (explicit assignment)  
**Status:** partial  
**Interface revision:** backend contracts v1

## Delivered

Added `scripts/check_backend_question.py` for one opt-in `/api/chat` question. It snapshots `data/knowledge.sqlite` using SQLite backup, independently reads the latest WELL-0001 inspection, uses temporary private memory, and validates each component against its cited saved result. The checker distinguishes a complete pass from `pass_with_limitations`; partial status is accepted only when the answer names the observation-date uncertainty and the operator note's unverified work order. `tests/test_backend_question.py` exercises this path with scripted providers and temporary data; no paid calls run in tests.

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `python3 -m pytest -q tests/test_backend_question.py` | pass | 4 passed; 16 installed FastAPI/Python 3.14 deprecation warnings |
| `python3 -m py_compile scripts/check_backend_question.py tests/test_backend_question.py` | pass | Both files compile. |
| Offline review of ignored `data/checks/q1-live-diagnostic.json` | partial | Model answer status is `partial`; all numeric card values match independent shared data: 25.6°C wellhead, 22.4°C ambient, 3.2°C delta, 15°C T200 threshold, producing=false, latest inspection INS-0001-0203 at 2026-10-15 09:45Z. Card and note table rows match their own cited complete, untruncated saved results. Required inspection, OM-T200 §9.3, and CTX-0001-003 sources resolve. The answer honestly states no newer inspection exists and that rod-string work has no maintenance work order. |
| Offline acceptance of saved answer | fail | Answer adds a factual counterweight-note claim in its limitations but omits citation CTX-0001-002. The harness rejects it with `answer mentions the counterweight note without citation CTX-0001-002`. Adding the already-resolved source citation to an in-memory copy yields `pass_with_limitations`; this was only a diagnostic simulation, not a change to the captured answer. |

## Limits and decisions needed

Root later provided a successful live answer snapshot for offline review; no further provider call was made. The answer's central state, numeric values, latest-inspection provenance, manual citation, planned-shut-in note/table and saved-result integrity pass. The `partial` label is warranted because there is no inspection after 15 October and the rod-string work order remains unverified. The answer is not accepted by this harness because it also introduces an uncited CTX-0001-002 counterweight-note claim. If the model cites that source, the same answer shape is correctly classified as `pass_with_limitations`, not upgraded to complete. No app files or live answer were altered.

## Handoff

Changed files are `scripts/check_backend_question.py`, `tests/test_backend_question.py`, and this report. Sol can reproduce the no-cost harness tests with the pytest command above. The harness prints fixed check names, accepts card-plus-supporting-component answers, validates all displayed rows against cited complete saved results, and can save an owner-only answer snapshot to ignored `data/checks/q1-live-diagnostic.json`. The existing snapshot is a private diagnostic artifact and must remain ignored. No broad question run or frontend implementation is included.

**Sol review:** Sol corrected the harness to allow a card plus supporting components and validate each component against its own saved result. Live Q1 core evidence is sound and partial status is justified; acceptance remains blocked by the uncited CTX-0001-002 claim. No paid rerun authorized for this review.

## Sol final acceptance

Full permissions restored DNS and catalog access. Root separated transport failures from invalid response formats, added safe regression coverage, and ran the actual router-backed question. Independent review found correct state/readings/results but a CTX-0001-002 mention omitted from citations. Root fixed the shared citation resolver for explicitly named record/manual IDs in all answer/caveat/conflict prose, with a regression test; this is not a Q1-specific application route.

The final live response used five kimi-k3 calls, took82317ms, and returned a supported partial answer. Against the real shared source: inspection INS-0001-0203, wellhead25.6C, ambient22.4C, delta3.2C, threshold15C, producing0. Its seven source citations resolve; its status-card data matches a complete retained query result. Work-order provenance and the time since the latest inspection remain explicit limitations.

The initial checker rejected different wording of these caveats (required the literal word 'after' and selected work-order phrases). Root removed those phrase checks, retained exact numeric/time/source/stored-row checks, and added a regression proving equivalent caveat wording passes while an incorrect production value still fails. Independent revalidation of the actual saved live response is **pass_with_limitations**. The original private snapshot was not rewritten to fake a complete answer; the validation summary is ignored data/checks/q1-live-validated.json. No further paid request was needed for that revalidation.

Checks: full backend suite70passed before the final checker-only regression; final tests/test_backend_question.py5passed. This accepts the Q1 data/source slice, not all18 questions or native OpenUI generation. Browser rendering remains untested; the observed82-second response is a demo latency concern.
