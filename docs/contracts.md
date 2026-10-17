# Shared contracts — agree before parallel work

Status: backend version 1 implemented; frontend pending. Sol owns this file and the code equivalents. A necessary change is reported to Sol, applied once and sent to all affected workers.

The backend endpoints/classes exist. Exact Python methods are in tasks/briefs/backend-interfaces.md. Keep Python and TypeScript definitions consistent. Do not treat this document as a reason to build unused helpers.

## HTTP surface

| Route | Request | Response / rule |
|---|---|---|
| `GET /api/health` | None | Ready state, active dataset version, analysis date; no secret settings |
| `GET /api/users` | None | `users`: IDs, names, roles, teams from the active shared data |
| `POST /api/threads` | `user_id` | New `thread_id` and owner |
| `GET /api/threads?user_id=...` | Selected demo user | Only that user’s thread summaries |
| `GET /api/threads/{id}/messages?user_id=...` | Selected demo user | Owned thread messages and saved answers |
| `POST /api/chat` | `request_id`, `user_id`, `thread_id`, `text` | Completed answer described below; validate thread ownership |
| `GET /api/results/{id}?user_id=...` | Selected demo user | Owned saved result, including paged/full detail where needed |
| `GET /api/evidence/{id}?user_id=...` | Selected demo user | Resolved citation; enforce ownership when it refers to private results |

User selection is a demo convention. Server checks ownership consistently but this is not authenticated multi-tenant security. User IDs in HTTP input are not model-controlled tool arguments. Conversation-date overrides belong in test fixtures, not model parameters.

## Completed answer

Required fields: `request_id`, `thread_id`, `message_id`, `analysis_date`, `status`, `answer`, `components`, `citations`, `conflicts`, `limitations`.

- `status`: `complete` or `partial`. A failed transport/provider call returns an error, not a fabricated completed answer.
- `answer`: plain explanation. Markdown is rendered safely, without arbitrary HTML.
- `components`: ordered list of the six component types below, possibly empty for a short fact answer.
- `citations`: resolved source references used by this answer. Unknown references are rejected or explicitly reported missing.
- `conflicts`: list of disagreeing statements, their sources/authors/times and current state; may be empty.
- `limitations`: missing/unread evidence, truncation or failed visuals; may be empty.
- `model` is the configured model/route; `served_models` retains actual serving model IDs in call order when routing is used.

Example shape, using placeholder references only:

```json
{
  "request_id": "request-1",
  "thread_id": "thread-1",
  "message_id": "message-2",
  "analysis_date": "2026-10-17",
  "status": "complete",
  "answer": "Explanation grounded in result R1.",
  "components": [
    {"id":"v1","type":"bar","title":"Downtime","result_id":"R1","mapping":{"category":"asset_id","value":"downtime_days"}},
    {"id":"v2","type":"table","title":"Details","result_id":"R1","mapping":{"columns":["asset_id","downtime_days"]}}
  ],
  "citations": [],
  "conflicts": [],
  "limitations": []
}
```

Actual factual answers require populated supporting citations; the example illustrates shape, not acceptable evidence completeness. Model drafts include response_kind (factual by default, or clarification). Factual answers require resolved citations; clarification is a question without factual components or an entity list. Conversation recall cites owned private message IDs. Total serialized model history is limited to 96,000 characters, with eight rounds and a 120-second wall-clock budget.

Model output contains component descriptions and reference IDs; the server resolves/validates them and never trusts copied row values.

## Component mappings

| Type | Required mapping | Display expectation |
|---|---|---|
| `card` | `fields`: list of result column names | One selected row; labeled values, units, observation time |
| `table` | `columns`: ordered result column names | Accessible table, empty state, optional sorting |
| `line` | `x`, `series` (column names); optional `inactive` boolean column | Time/date labels, units, legend, inactive markers |
| `bar` | `category`, `value` | Labels, units, ties preserved |
| `map` | `lat`, `lon`, `label`; optional `details` column names | Geographic points, popups, coordinate/details alternative |
| `heatmap` | `x`, `y`, `value` | Two dimensions, count/color legend and explicit zero cells |

Validate that columns exist and types fit. Every component has `id`, `type`, `title`, `result_id` and `mapping`. Server results carry column labels/units. Card results contain one row; return an error for an ambiguous selection rather than silently picking one. Cap components per answer at six in v1 to bound rendering, while allowing any required single visual. No arbitrary component names, external URLs, scripts or HTML from the model.

## Saved query result

`result_id`, owner user/thread, columns (name/type/label/unit), `rows`, `returned_rows`, `total_rows` when known, `truncated`, `complete`, `limitations`, `evidence_refs`, `analysis_date`, `dataset_version`, `knowledge_revision`.

Save the query/parameters and contributing record IDs, or a reproducible contributor query against a retained source version. Each accepted shared write increments the knowledge revision. Saved old answers retain their old result/revision and remain labeled historical; new answers query current corrected values. Do not mutate a past answer’s chart behind its prose.

Large output can be paged; a preview is never an aggregate’s input. Large results stay stored outside the prompt and can be reopened. Any result/history lookup enforces ownership before returning content.

## Tool boundary

`run_sql(sql, params)` returns the saved-result shape/reference plus a bounded preview. Only approved corrected views/lookups are queryable. `get_evidence(refs)` opens known shared source IDs/sections or owned result/private-message evidence. `search_documents(query, filters)` returns shared source IDs and excerpts, with clear search/coverage limits.

`memory_read(query)` and `remember(kind, payload)` receive user/thread context from server code, never a model-supplied user ID. `remember` accepts `shared_claim`, `field_override` or `rule_override` and validates target, type, scope, dates and reason. It returns a persistent ID, acceptance state, affected target and any visible disagreement. Deduplicate by user/request and semantic change target across retries, independent of provider tool-call IDs.

Use explicit errors: `invalid_request`, `forbidden`, `not_found`, `query_rejected`, `timeout`, `provider_error`, `incomplete_evidence`, with a safe readable message. Never return credentials or a traceback to the browser. Workers must not change an unknown/partial result into a successful empty result.

## Python boundaries to freeze at T1

Keep domain reads independent of private storage. The following small boundary is the starting contract; Sol records any necessary revision before dispatch:

| Class method / function | Returns / responsibility |
|---|---|
| `load.load_dataset(root, knowledge_path)` | Load summary with counts, version, collisions and coverage; no provider calls |
| `KnowledgeStore.query_shared(sql, params)` | Validated shared rows, column metadata and evidence; no private-result persistence |
| `KnowledgeStore.get_shared_evidence(refs)` | Shared source records/document spans |
| `KnowledgeStore.apply_shared_change(change, author_id, request_key)` | Checked persistent change, revision and conflicts; called only by the server tool adapter |
| `MemoryStore.load_context(user_id, thread_id, query)` | Only permitted private messages and exact entity references |
| `MemoryStore.save_result(user_id, thread_id, shared_rows)` | Owned result reference/rows with source and knowledge revisions |
| `Copilot.answer(context, text)` | Calls the permitted tools and returns a checked answer description |

Sol’s tool/API adapter connects shared rows to private result persistence. A data worker does not need to read private memory to implement a shared query. All private message/result access stays behind the memory ownership checks. Shared-change validation belongs beside the corrected store logic, not in frontend code.

## Correction scope and precedence

Allowed scopes are `inspection`, `well` and `well_type`; `target_id` must resolve to that kind of entity. Measured fields (`wellhead_temp_c`, `ambient_temp_c`, `spill_detected`, `spill_est_volume_bbl`) use inspection scope. Rule changes use well or well-type scope and an explicit rule key; `rca_count` additionally requires an `equipment_kind`. A claim has a well ID and text/validity dates, but no numeric override semantics.

Baseline source facts/corrections apply first. For a particular rule, a matching well override is more specific than a matching type override. For the same exact target/rule/field and dates, conflicting accepted-value proposals require explicit resolution; retain the previously accepted value and report the unresolved proposal. Do not silently use “latest timestamp wins”. Keep every version and the author/reason.

Q14 therefore targets scope `well_type`, target `T350`, rule `rca_count`, equipment `pump_jack`, value 2. It cannot change other equipment or T200. Q12 targets only INS-0164-0205’s wellhead temperature; Q13 targets only INS-0151-0201’s volume. Arbitrary fields or ambiguous targets are rejected for clarification.

## Analytics SQL boundary

Freeze these normal query names at T1: `assets`, `equipment`, `areas`, `teams`, `users`, `effective_inspections`, `latest_inspections`, `effective_rules`, `maintenance`, `regulatory_events`, `source_notes`, `shared_claims`, `report_facts`, and `report_checks`. Report check columns are explicitly the author’s reported result, not an automatically current verdict. Runtime raw source tables are not directly exposed through this tool.

Use a separate connection opened read-only against the shared DB, with query-only mode, SQLite authorization checks, disabled extensions and an execution/output limit. Deny writes, schema changes, attachment, PRAGMA and unapproved functions. Permit underlying raw-table reads only when SQLite identifies an approved corrected view as their source; do not rely on a SELECT-prefix regex. The private DB is never attached. The dedicated evidence/search tools use checked IDs and their own fixed queries rather than granting extra SQL access.

Sol freezes the small required built-in function allowlist with the store implementation (aggregates, date/string helpers and window functions actually used). Check rejected writes/attachment/extension calls and direct raw/private access, as well as a legitimate query through an approved view. Return safe diagnostics so the model can repair a mistaken column/query without weakening this boundary.
