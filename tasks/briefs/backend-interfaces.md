# Backend Python contract v1 — frozen for current assignments

Use plain JSON-compatible dictionaries and app.errors.AppError(code, message, status_code=400). All methods sync; each DB operation owns/closes its connection. Paths passed explicitly to stores. No worker edits app/errors.py, API/contracts/provider/agent, requirements, pytest.ini or another worker’s files.

## Shared data: app.store.KnowledgeStore(path, analysis_date="2026-10-17")

- info() -> {dataset_version:str, knowledge_revision:int, analysis_date:str, counts:dict}.
- users() -> list[dict] including user_id,name,role,team_id.
- schema_text() -> concise public SQL schema including columns.
- rules_text() -> all five source rule documents with IDs/headings.
- query_shared(sql, params=None) -> SharedRows.
- get_shared_evidence(refs:list[str]) -> list[Evidence]. Reject unknown refs with not_found.
- search_documents(query:str, filters:dict|None=None) -> {matches:list, complete:bool, limitations:list}.
- apply_shared_change(change:dict, author_id:str, request_key:str) -> {change_id,status,knowledge_revision,conflicts:list, ...}. Confirm author exists.
- app.load.load_dataset(root, knowledge_path) -> load summary. CLI python -m app.load ROOT --db PATH.

SharedRows: columns:list[{name,type,label,unit}], rows:list[dict], returned_rows:int, total_rows:int|null, truncated:bool, complete:bool, limitations:list[str], evidence_refs:list[str], analysis_date,dataset_version,knowledge_revision, query:{sql,params}. Bounded rows ≤1000, timeout. Do not drop aggregate inputs. Retain a contributor recipe/query for aggregates. Evidence: {id,kind,title,source_path,content} plus optional metadata; IDs may be record ID or doc-ID#section. No arbitrary paths. Public SQL names from docs/contracts.md; expose record IDs/units and corrected values; preserve raw evidence. Store may own schema helpers in assigned files only.

remember change kinds: shared_claim, field_override, rule_override. Fields: kind,scope (inspection|well|well_type),target_id,field (measurement or rule key),value,reason, optional equipment_kind/valid_from/valid_to/text. Measurements inspection-only; rca_count well/type requires equipment_kind. Accept explicit corrections over raw; two conflicting runtime proposals for same target need explicit supersedes_id to replace old accepted value, else pending conflict. Shared claim well-only and never silently overrides readings.

## Private data: app.memory.MemoryStore(path)

- create_thread(user_id)->{thread_id,user_id,title,created_at}.
- list_threads(user_id)->list[dict].
- get_thread(user_id,thread_id)->dict; ownership checked.
- append_message(user_id,thread_id,role,text,*,answer=None,entity_ids=None,created_at=None)->dict. Roles user/assistant; created_at test override only.
- messages(user_id,thread_id)->list[dict] with role,text,message_id,created_at,answer,entity_ids.
- get_message(user_id,message_id)->Evidence; owner-scoped private conversation citation.
- load_context(user_id,thread_id,query="")->dict of recent current messages and earlier references/turns for this user only; exact discussed IDs, timestamps; bounded prompt size.
- save_result(user_id,thread_id,shared_rows)->dict with result_id plus SharedRows. No token-saving mutation of saved data.
- get_result(user_id,result_id)->dict, user/thread ownership checked.
- start_request(user_id,thread_id,request_id,text)->cached completed answer dict or None. Atomically register a new request; mismatched owner/thread/text rejects. Existing in-progress rejects busy; failed may retry. Append user turn exactly once.
- finish_request(user_id,thread_id,request_id,answer)->saved completed answer; append assistant once, assign message_id, retain exact discussed entity IDs from answer/results.
- fail_request(user_id,thread_id,request_id)->None marks retryable failure. No silent duplication of turns.
- save_trace(user_id,thread_id,request_id,tool,arguments,outcome)->None; separate from chat context, bounded/tool summaries.

Cross-user attempts return forbidden403 or not_found404 consistently. Parameterized SQLite; private store never imported by shared SQL. Independent tests use temp DBs. Do not require frontend/provider/network.
