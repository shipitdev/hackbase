import json

import pytest
from pydantic import ValidationError

from app.agent import Copilot, EvidenceArgs, _compact_history, _preview
from app.errors import AppError


class Memory:
    def __init__(self):
        self.results = {}

    def load_context(self, *args):
        return {"messages": [], "references": []}

    def save_result(self, user, thread, result):
        result = {**result, "result_id": f"R{len(self.results) + 1}", "user_id": user, "thread_id": thread}
        self.results[result["result_id"]] = result
        return result

    def get_result(self, user, result_id):
        if result_id not in self.results:
            raise AppError("not_found", "Result not found", 404)
        return self.results[result_id]

    def save_trace(self, *args):
        pass


class Knowledge:
    def __init__(self):
        self.reopened = []

    def schema_text(self):
        return "effective_inspections(asset_id, producing)"

    def rules_text(self):
        return "x" * 26000

    def query_shared(self, sql, params=None):
        columns = [{"name": f"field_{i}", "type": "text", "label": f"Field {i}", "unit": None} for i in range(35)]
        rows = [{f"field_{i}": f"evidence-{i}-" + "x" * 250 for i in range(35)} for _ in range(5)]
        return {"columns": columns, "rows": rows, "returned_rows": 5, "total_rows": 5,
                "evidence_refs": ["INS-0001-0203", "OM-T200#9.3"], "complete": True,
                "truncated": False, "limitations": [], "analysis_date": "2027-01-15",
                "dataset_version": "test", "knowledge_revision": 0}

    def search_documents(self, query, filters=None):
        return {"matches": [{"id": "OPS-2", "kind": "document", "title": "Flowline operating procedure",
                             "source_path": "fleet/sops/ops-2.md", "excerpt": "Current bypass and exception guidance."}],
                "complete": True, "limitations": []}

    def get_shared_evidence(self, refs):
        self.reopened.extend(refs)
        return [{"id": ref, "kind": "document_section", "title": ref, "content": "OPS-2 source text " + "s" * 1200} for ref in refs]


class Replay:
    model = "offline"

    def __init__(self):
        self.requests = []
        self.round = 0

    def complete(self, messages, tools, **kwargs):
        self.requests.append(json.loads(json.dumps(messages, ensure_ascii=False)))
        round_index = self.round
        self.round += 1
        if round_index < 3:
            calls = []
            for i in range(8):
                if round_index == 1 and i == 0:
                    name, args = "search_documents", {"query": "flowline bypass"}
                elif round_index == 1 and i == 1:
                    name, args = "get_evidence", {"refs": ["OPS-2"]}
                else:
                    name, args = "run_sql", {"sql": "SELECT * FROM effective_inspections"}
                calls.append({"id": f"r{round_index}-{i}", "type": "function",
                              "function": {"name": name, "arguments": json.dumps(args)}})
            return {"message": {"role": "assistant", "tool_calls": calls}, "usage": {}}
        return {"message": {"role": "assistant", "content": json.dumps({
            "answer": "I found the current source and saved query result; the result rows are available for review.",
            "ui": None, "citation_refs": ["OPS-2"], "conflicts": [], "limitations": [], "entity_ids": []
        })}, "usage": {}}


def test_saved_result_reopen_preview_keeps_reference_schema_and_count():
    result = {"id": "R-PRIVATE", "kind": "query_result", "content": {
        "result_id": "R-PRIVATE", "columns": [{"name": "asset_id"}], "returned_rows": 800,
        "rows": [{"asset_id": f"WELL-{i}", "payload": "x" * 5000} for i in range(20)],
        "evidence_refs": ["INS-0001-0203"], "complete": False, "truncated": True,
    }}
    preview = json.loads(_preview([result]))[0]["content"]
    assert preview["result_id"] == "R-PRIVATE"
    assert preview["columns"] == [{"name": "asset_id"}]
    assert preview["returned_rows"] == 800 and preview["truncated"] is True
    assert len(_preview([result])) < 5000


def test_wide_sql_preview_and_compaction_keep_result_metadata_structured():
    result = {"result_id": "R-WIDE", "columns": [{"name": f"column_{i}", "type": "text", "label": f"Column {i}", "unit": None} for i in range(100)],
              "rows": [{f"column_{i}": "x" * 300 for i in range(100)}], "returned_rows": 801,
              "total_rows": 1000, "complete": False, "truncated": True,
              "evidence_refs": ["INS-0001-0203", "OM-T200#9.3"]}
    preview = json.loads(_preview(result))
    assert len(_preview(result)) <= 5000
    assert preview["result_id"] == "R-WIDE" and preview["returned_rows"] == 801
    assert preview["columns"] and preview["evidence_refs"] == result["evidence_refs"]
    assert preview["omitted_column_count"] > 0

    messages = [
        {"role": "system", "content": "x" * 73000}, {"role": "user", "content": "current question"},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "old", "type": "function", "function": {"name": "run_sql", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "old", "content": _preview(result)},
        {"role": "assistant", "content": None, "tool_calls": [{"id": "new", "type": "function", "function": {"name": "run_sql", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "new", "content": "{}"},
    ]
    compacted = _compact_history(messages)
    catalog = json.dumps(compacted[0], ensure_ascii=False)
    assert "R-WIDE" in catalog and "returned_rows" in catalog and "evidence_refs" in catalog
    assert "old" not in json.dumps(compacted[2:], ensure_ascii=False)


def test_evidence_pages_include_later_source_text_and_allow_re_reads():
    documents = [
        {"id": "MOC-1", "kind": "document", "title": "MOC", "content": {"sections": [
            {"id": "MOC-1#1", "heading": "Bypass", "content": "a" * 2400 + "CRITICAL MOC TEXT" + "b" * 500}
        ]}},
        {"id": "SOP-1#2", "kind": "document_section", "title": "SOP section", "content": "c" * 2400 + "CRITICAL SOP TEXT" + "d" * 500},
    ]
    first = json.loads(_preview(documents, offset=0, limit=6000))
    assert [item["id"] for item in first] == ["MOC-1", "SOP-1#2"]
    assert all(len(item["content"]) == 1750 for item in first)
    assert all(item["next_offset"] == item["offset"] + len(item["content"]) for item in first)

    second = json.loads(_preview(documents, offset=first[0]["next_offset"], limit=6000))
    assert "CRITICAL MOC TEXT" in second[0]["content"]
    assert "CRITICAL SOP TEXT" in second[1]["content"]
    repeated = json.loads(_preview(documents, offset=0, limit=6000))
    assert repeated[0]["content"] == first[0]["content"]
    assert len(_preview(documents, offset=0, limit=6000)) <= 5000


def test_evidence_page_arguments_have_bounded_compatible_defaults():
    assert EvidenceArgs.model_validate({"refs": ["MOC-1"]}).model_dump() == {"refs": ["MOC-1"], "offset": 0, "limit": 3000}
    for value in ({"refs": ["MOC-1"], "offset": -1}, {"refs": ["MOC-1"], "limit": 6001}):
        with pytest.raises(ValidationError):
            EvidenceArgs.model_validate(value)


def test_tool_evidence_offset_fetches_next_page_and_repeat_is_not_deduped():
    class PageKnowledge(Knowledge):
        def get_shared_evidence(self, refs):
            self.reopened.extend(refs)
            return [
                {"id": ref, "kind": "document", "title": ref,
                 "content": ("a" if ref == "MOC-1" else "b") * 2400 + f"CRITICAL {ref} TEXT" + "z" * 400}
                for ref in refs
            ]

    class PageProvider:
        model = "offline"
        def __init__(self): self.requests = []
        def complete(self, messages, tools, **kwargs):
            self.requests.append(json.loads(json.dumps(messages, ensure_ascii=False)))
            if len(self.requests) == 1:
                return {"message": {"role": "assistant", "tool_calls": [{"id": "page-1", "type": "function", "function": {"name": "get_evidence", "arguments": json.dumps({"refs": ["MOC-1", "SOP-1"], "offset": 0, "limit": 6000})}}]}, "usage": {}}
            if len(self.requests) in (2, 3):
                prior = json.loads(messages[-1]["content"])
                offset = prior[0]["next_offset"] if len(self.requests) == 2 else 0
                return {"message": {"role": "assistant", "tool_calls": [{"id": f"page-{len(self.requests)}", "type": "function", "function": {"name": "get_evidence", "arguments": json.dumps({"refs": ["MOC-1", "SOP-1"], "offset": offset, "limit": 6000})}}]}, "usage": {}}
            return {"message": {"role": "assistant", "content": json.dumps({"answer": "The cited MOC supports the assessment.", "ui": None, "citation_refs": ["MOC-1"], "conflicts": [], "limitations": [], "entity_ids": []})}, "usage": {}}

    knowledge, provider = PageKnowledge(), PageProvider()
    answer = Copilot(knowledge, Memory(), provider).answer({"user_id": "U-1", "thread_id": "T1", "request_id": "page", "analysis_date": "2027-01-15"}, "Assess the MOC.")
    first = json.loads(provider.requests[1][-1]["content"])
    second = json.loads(provider.requests[2][-1]["content"])
    repeated = json.loads(provider.requests[3][-1]["content"])
    assert first[0]["next_offset"] == len(first[0]["content"])
    assert "CRITICAL MOC-1 TEXT" in second[0]["content"]
    assert repeated[0]["content"] == first[0]["content"]
    assert answer["status"] == "complete" and answer["citations"][0]["id"] == "MOC-1"


def test_broad_repeated_tool_replay_compacts_and_keeps_grounded_context():
    memory, knowledge, provider = Memory(), Knowledge(), Replay()
    copilot = Copilot(knowledge, memory, provider)
    question = "WELL-0001's reading was corrected to 41 C. Assess current flowline bypasses and preserve that correction's scope."
    answer = copilot.answer({"user_id": "U-1", "thread_id": "T1", "request_id": "q1", "analysis_date": "2027-01-15"}, question)

    sizes = [len(json.dumps(messages, ensure_ascii=False)) for messages in provider.requests]
    assert max(sizes) <= 96000
    assert sizes[-1] < 72000
    final_context = json.dumps(provider.requests[-1], ensure_ascii=False)
    assert question in final_context
    assert "COMPACTED EVIDENCE CATALOG" in final_context
    assert "R1" in final_context and "columns" in final_context and "returned_rows" in final_context
    assert knowledge.reopened.count("OPS-2") >= 1
    assert answer["status"] == "complete" and answer["citations"][0]["id"] == "OPS-2"

    for messages in provider.requests:
        pending = 0
        for message in messages[2:]:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                assert pending == 0
                pending = len(message["tool_calls"])
            elif message.get("role") == "tool":
                assert pending > 0
                pending -= 1
            elif pending:
                assert pending == 0
        assert pending == 0


def test_document_body_limitations_and_claim_attribution_survive_preview():
    from app.agent import _source_text
    assert _source_text({"content": "MOC approval details", "sections": []}) == "MOC approval details"
    source = [{"id": "change:CHG-1", "kind": "shared_claim", "content": "Pump reportedly replaced", "metadata": {"author_id": "U-601", "status": "accepted"}}]
    assert json.loads(_preview(source))[0]["metadata"]["author_id"] == "U-601"
    result = {"result_id": "R1", "rows": [], "columns": [], "limitations": ["Missing evidence is unknown"]}
    assert json.loads(_preview(result))["limitations"] == ["Missing evidence is unknown"]
