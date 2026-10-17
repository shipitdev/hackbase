import pytest

from app.errors import AppError
from app.memory import MemoryStore


def shared_rows():
    return {
        "columns": [{"name": "well_id", "type": "text", "label": "Well", "unit": None}],
        "rows": [{"well_id": "WELL-0121"}, {"well_id": "WELL-0138"}, {"well_id": "WELL-0107"}],
        "returned_rows": 3,
        "total_rows": 3,
        "truncated": False,
        "complete": True,
        "limitations": [],
        "evidence_refs": ["INS-0121-0200"],
        "analysis_date": "2026-10-16",
        "dataset_version": "sample-v1",
        "knowledge_revision": 0,
        "query": {"sql": "SELECT well_id FROM assets", "params": []},
    }


def test_private_threads_results_and_context_survive_restart(tmp_path):
    path = tmp_path / "memory.sqlite"
    store = MemoryStore(path)
    thread = store.create_thread("michael")
    store.append_message("michael", thread["thread_id"], "assistant", "Top wells", entity_ids=["WELL-0121", "WELL-0138", "WELL-0107"])
    result = store.save_result("michael", thread["thread_id"], shared_rows())

    reopened = MemoryStore(path)
    context = reopened.load_context("michael", reopened.create_thread("michael")["thread_id"], "repair costs")
    assert {"WELL-0121", "WELL-0138", "WELL-0107"}.issubset(set(context["entity_ids"]))
    assert context["references"]
    assert reopened.get_result("michael", result["result_id"])["rows"] == shared_rows()["rows"]
    with pytest.raises(AppError) as exc:
        reopened.get_result("jessica", result["result_id"])
    assert exc.value.code in {"forbidden", "not_found"}


def test_request_retries_are_idempotent_and_cached(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    thread_id = store.create_thread("michael")["thread_id"]
    assert store.start_request("michael", thread_id, "r1", "Q6") is None
    assert store.get_thread("michael", thread_id)["title"] == "Q6"
    with pytest.raises(AppError) as exc:
        store.start_request("michael", thread_id, "r1", "different")
    assert exc.value.code == "invalid_request"
    with pytest.raises(AppError) as exc:
        store.start_request("michael", thread_id, "r1", "Q6")
    assert exc.value.code == "busy"
    store.save_result("michael", thread_id, shared_rows())
    saved = store.finish_request("michael", thread_id, "r1", {"answer": "cached", "entity_ids": ["WELL-0121"]})
    assert store.start_request("michael", thread_id, "r1", "Q6") == saved
    assert [m["role"] for m in store.messages("michael", thread_id)] == ["user", "assistant"]


def test_failed_request_retries_without_duplicate_turn_and_traces_stay_private(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    thread_id = store.create_thread("michael")["thread_id"]
    store.start_request("michael", thread_id, "r1", "question")
    store.save_trace("michael", thread_id, "r1", "run_sql", {"sql": "secret"}, {"rows": 3})
    store.fail_request("michael", thread_id, "r1")
    assert store.start_request("michael", thread_id, "r1", "question") is None
    assert [m["role"] for m in store.messages("michael", thread_id)] == ["user"]
    context = store.load_context("michael", thread_id)
    assert "secret" not in repr(context)


def test_only_answer_results_contribute_well_ids(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    thread_id = store.create_thread("michael")["thread_id"]
    store.start_request("michael", thread_id, "r1", "first")
    first = shared_rows()
    first["evidence_refs"] = ["INS-0121-0200"]
    old = store.save_result("michael", thread_id, first)
    store.finish_request("michael", thread_id, "r1", {"answer": "first", "components": [{"result_id": old["result_id"]}]})

    store.start_request("michael", thread_id, "r2", "second")
    second = {**shared_rows(), "rows": [{"well_id": "WELL-0999"}], "evidence_refs": ["INS-0999-0001"]}
    current = store.save_result("michael", thread_id, second)
    store.finish_request("michael", thread_id, "r2", {
        "answer": "second", "entity_ids": ["WELL-2000"],
        "components": [{"result_id": current["result_id"]}],
    })

    latest = store.messages("michael", thread_id)[-1]
    assert set(latest["entity_ids"]) == {"WELL-0999", "WELL-2000"}


def test_context_uses_discussed_results_not_undisplayed_queries(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    old_thread = store.create_thread("michael")["thread_id"]
    hidden = {**shared_rows(), "rows": [{"well_id": "WELL-X"}]}
    store.save_result("michael", old_thread, hidden)
    store.start_request("michael", old_thread, "r1", "Show WELL-Y")
    shown = {**shared_rows(), "rows": [{"well_id": "WELL-Y"}]}
    result = store.save_result("michael", old_thread, shown)
    store.finish_request("michael", old_thread, "r1", {"answer": "WELL-Y", "components": [{"result_id": result["result_id"]}]})

    new_thread = store.create_thread("michael")["thread_id"]
    context = store.load_context("michael", new_thread)
    assert "WELL-Y" in context["entity_ids"]
    assert "WELL-X" not in context["entity_ids"]


def test_distinct_in_progress_request_is_rejected_per_thread(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    first = store.create_thread("michael")["thread_id"]
    other = store.create_thread("michael")["thread_id"]
    store.start_request("michael", first, "r1", "one")
    with pytest.raises(AppError) as exc:
        store.start_request("michael", first, "r2", "two")
    assert exc.value.code == "busy" and exc.value.status_code == 409
    assert store.start_request("michael", other, "r3", "other thread") is None


def test_thread_ownership_is_checked(tmp_path):
    store = MemoryStore(tmp_path / "memory.sqlite")
    thread_id = store.create_thread("michael")["thread_id"]
    with pytest.raises(AppError) as exc:
        store.messages("jessica", thread_id)
    assert exc.value.code in {"forbidden", "not_found"}


def test_private_message_citations_are_owner_scoped(tmp_path):
    memory=MemoryStore(tmp_path/'private.sqlite')
    thread=memory.create_thread('U-1')
    message=memory.append_message('U-1',thread['thread_id'],'user','Earlier discussion')
    assert memory.get_message('U-1',message['message_id'])['content']['text']=='Earlier discussion'
    with pytest.raises(AppError):
        memory.get_message('U-2',message['message_id'])
