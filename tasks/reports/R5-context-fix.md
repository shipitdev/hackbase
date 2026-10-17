# Worker report: R5 runtime context repair

**Status:** complete for orchestrator review
**Files changed:** `app/agent.py`, `tests/test_context_budget.py`

The tool loop now sends bounded structured previews while saved query rows and source records remain in their existing stores. SQL previews retain result IDs, column metadata, row counts, completeness, limitations and a capped evidence-reference catalog; very wide schemas list omitted column counts instead of collapsing metadata into a truncated JSON string. Search previews deduplicate repeated IDs and keep excerpts short. Explicit `get_evidence` reads always return the requested text page; optional `offset` and `limit` fields expose `content_length`, `next_offset` and truncation state in the prompt preview. Multi-reference reads bound the combined text payload while preserving every source ID. The preview only is paged: answer citation resolution still receives the full source object, and saved rows remain unchanged. Whole-document payloads with `sections` are rendered as heading and content text before paging.

At 72,000 serialized provider-context characters, completed older tool-call batches are removed as whole assistant/tool-reply groups. Their saved result IDs, columns, row counts, completeness, citation references and source catalog move into a system-message summary. The exact current user request remains in the conversation. If the retained batch still exceeds the proactive target, its tool replies are reduced to metadata while preserving every call ID and matching tool reply. The 96,000-character hard cap, eight rounds, eight tools per batch, existing repair handling and provider tool-choice behavior remain in place. Context sizing uses the provider’s normal JSON serialization, including spaces.

## Offline replay

The R5 replay sent three batches of eight broad fake SQL/search/evidence calls, including repeated source IDs and oversized saved rows, followed by a grounded final answer. The base prompt was **35,973 characters**, with provider contexts **35,973 → 67,141 → 66,443 → 52,946 characters**. Peak context was 67,141 characters; the answer completed with its source citation. The replay verified the current request and correction text survived compaction, source evidence could be reopened, result IDs/columns/counts remained in the catalog, and no tool-call groups were orphaned.

For the E4 Q4 case, the recorded pre-fix path had a 37,573-character base prompt, three search previews of 11,873, 11,873 and 5,741 characters (the first two repeated the same four documents), plus roughly 20,000 characters of SQL previews and assistant/tool-call content. It reached the 96,000-character hard stop before a verified answer. These figures are the existing E4 trace summarized in the R5 assignment; no live replay or paid provider call was made for this fix.

## Checks

| Command | Outcome |
|---|---|
| `pytest -q tests/test_agent.py tests/test_store.py tests/test_context_budget.py` | 40 passed in 35.28s, including bounded page arguments, paging, repeat-read, wide-result metadata and compaction-catalog checks. |
| Offline replay script using `tests/test_context_budget.py` fixtures | Completed; 35,973-character base prompt, peak context 67,141 characters, one citation, complete answer. |

The owned-result/foreign-thread rejection test passed in the first focused run, and the full agent/store/context test command passed. No live evaluation, active database mutation or paid provider call was run. `app/store.py` required no change because complete results and ownership checks were already available through the existing store API.

**Limits:** the compact catalog includes at most the first 30 evidence references from each saved query preview; larger result evidence remains saved and can be reopened by result ID. Evidence preview text is bounded to 3,500 characters total across references and 5,000 serialized characters overall. A result with many references or an unusually wide schema may require another focused read; omitted rows/columns remain saved and are identified as omitted.

**Sol review:** accepted after review fixes. Root preserved full nested document text, query limitations and shared-claim attribution in previews, and added a focused preservation test. Final provider/agent/store/context suite:75passed in35.43s. BackendPID39673 restarted; one isolated Q4 live check authorized, pending. No E4 score change.
