import json
from types import SimpleNamespace

from scripts.evaluate_questions import (
    SCENARIOS,
    conversation_timestamp,
    dependency_gate,
    may_start_step,
    qualify_legacy_thread,
    reconcile_step,
    scenario_clock,
    step_capture_status,
    submit_once,
    thread_key,
    run_step,
    safe_evaluation_metadata,
)


class FakeResponse:
    status_code = 200

    def json(self):
        return {"status": "partial", "answer": "Some evidence", "served_models": ["fake"], "usage": {}}


class FakeErrorResponse:
    status_code = 504

    def json(self):
        return {"evaluation_metadata": {"served_models": ["fake"], "usage": {"total_tokens": 9, "bad": True},
                                         "latency_ms": 55, "secret": "never capture"}}


class FakeClient:
    def __init__(self, raises=False, response=None):
        self.calls = []
        self.raises = raises
        self.response = response or FakeResponse()

    def post(self, path, json):
        self.calls.append((path, json))
        if self.raises:
            raise TimeoutError("lost response")
        return self.response


def test_partial_http_200_is_captured_answer_not_correctness_pass():
    assert step_capture_status(200, {"status": "partial", "answer": "text"}) == "answer_captured"
    assert step_capture_status(200, {"status": "partial", "answer": ""}) == "response_without_answer"
    assert step_capture_status(504, {}) == "http_error_no_answer"


def test_attempt_is_fenced_before_submit_and_never_auto_replayed(tmp_path):
    client = FakeClient()
    state = {"steps": {}}
    item = {"name": "Qx", "user": "U-1", "day": "2026-10-17", "text": "question", "visual": None}
    submit_once(client, tmp_path, state, "Qx", item, "request-1", {"request_id": "request-1"})

    assert len(client.calls) == 1
    assert state["steps"]["Qx"]["status"] == "answer_captured"
    assert not may_start_step(state, "Qx")
    assert json.loads((tmp_path / "Qx.json").read_text())["response"]["status"] == "partial"


def test_interrupted_submit_requires_manual_review_and_is_not_replayed(tmp_path):
    client = FakeClient(raises=True)
    state = {"steps": {}}
    item = {"name": "Qx", "user": "U-1", "day": "2026-10-17", "text": "question", "visual": None}

    try:
        submit_once(client, tmp_path, state, "Qx", item, "request-1", {"request_id": "request-1"})
    except TimeoutError:
        pass
    else:
        raise AssertionError("fake transport failure should propagate")

    assert len(client.calls) == 1
    assert state["steps"]["Qx"]["status"] == "manual_review"
    assert not may_start_step(state, "Qx")


def test_crash_pending_attempt_is_reconciled_without_replay():
    state = {"steps": {"Qx": {"status": "attempt_pending", "request_id": "request-1"}}}

    assert not reconcile_step(state, "Qx")
    assert state["steps"]["Qx"]["status"] == "manual_review"
    assert "replay is disabled" in state["steps"]["Qx"]["reason"]


def test_dependency_requires_saved_setup_or_confirmed_shared_write(tmp_path):
    request_id = "e1-Q16-Q16-share"
    state = {"steps": {"Q16-share": {"status": "http_error_no_answer", "request_id": request_id}}}
    client = FakeClient(response=FakeErrorResponse())
    item = {"name": "Q16-share", "user": "U-102", "day": "2026-10-17", "text": "plan", "visual": None}
    submit_once(client, tmp_path, state, "Q16", item, request_id, {"request_id": request_id})
    assert state["steps"]["Q16-share"]["served_models"] == ["fake"]
    assert state["steps"]["Q16-share"]["usage"] == {"total_tokens": 9}
    assert state["steps"]["Q16-share"]["latency_ms"] == 55

    import sqlite3
    db = sqlite3.connect(tmp_path / "knowledge.sqlite")
    db.execute("CREATE TABLE changes(request_key TEXT, status TEXT)")
    db.execute("INSERT INTO changes VALUES(?, 'accepted')", ("U-102:" + request_id + ":hash",))
    db.commit()
    db.close()
    assert dependency_gate(tmp_path, state, "Q16", ["Q16-share"]) == ("ready", [])


def test_missing_prior_entity_setup_is_manual_review_not_success(tmp_path):
    item = {"name": "Q6", "user": "U-201", "day": "2026-10-17", "text": "list wells", "visual": "bar"}
    state = {"steps": {"Q6": {"status": "response"}}}
    (tmp_path / "Q6.json").write_text(json.dumps({"response": {"status": "partial", "answer": "Could not verify", "entity_ids": []}}))

    assert dependency_gate(tmp_path, state, "Q6Q11", ["Q6"]) == ("manual_review", ["Q6"])


def test_q6_requires_exact_saved_memory_list(tmp_path):
    (tmp_path / "Q6.json").write_text(json.dumps({"response": {
        "entity_ids": ["WELL-0121", "WELL-0138", "WELL-0107", "WELL-9999"]
    }}))
    assert dependency_gate(tmp_path, {"steps": {"Q6": {"status": "response"}}}, "Q6Q11", ["Q6"]) == ("manual_review", ["Q6"])


def test_scenario_clock_restores_and_turns_are_ordered():
    module = SimpleNamespace(_now=lambda: "real")
    with scenario_clock(module, conversation_timestamp("2026-10-17", 0)):
        first = module._now()
        second = module._now()
        assert second > first
        assert module._now() > second
    assert module._now() == "real"
    assert conversation_timestamp("2026-10-17", 1) > first
    assert thread_key("U-1", "new") != thread_key("U-2", "new")


def test_run_step_uses_real_testclient_and_restores_unique_message_times(tmp_path, monkeypatch):
    import app.agent
    import app.provider
    import app.store
    import app.memory

    class FakeProvider:
        configured = True
        model = "offline-fake"

    class FakeKnowledge:
        def __init__(self, *_args, **_kwargs):
            pass

        def users(self):
            return [{"user_id": "U-202"}]

    monkeypatch.setattr(app.provider, "CompatibleProvider", FakeProvider)
    monkeypatch.setattr(app.store, "KnowledgeStore", FakeKnowledge)
    monkeypatch.setattr(app.agent.Copilot, "answer", lambda _self, context, _text: {
        "request_id": context["request_id"], "thread_id": context["thread_id"],
        "analysis_date": context["analysis_date"], "status": "complete", "answer": "offline answer",
        "components": [], "citations": [], "conflicts": [], "limitations": [], "entity_ids": ["WELL-0001"],
    })
    original_now = app.memory._now
    state = {"threads": {}, "steps": {}}
    run_step("Q1", tmp_path, state, SCENARIOS["Q1"][0])

    assert app.memory._now is original_now
    thread_id = state["threads"]["U-202:new"]
    from app.memory import MemoryStore
    messages = MemoryStore(tmp_path / "memory.sqlite").messages("U-202", thread_id)
    user, assistant = messages
    assert [user["role"], assistant["role"]] == ["user", "assistant"]
    assert user["created_at"] < assistant["created_at"]
    assert user["created_at"] != assistant["created_at"]


def test_safe_evaluation_metadata_captures_only_expected_fields():
    body = {"evaluation_metadata": {"served_models": ["fake"], "usage": {"total_tokens": 7, "bad": True},
                                    "latency_ms": 123.5, "secret": "skip"}}
    assert safe_evaluation_metadata(body) == {"served_models": ["fake"], "usage": {"total_tokens": 7}, "latency_ms": 123.5}


def test_legacy_thread_is_migrated_only_when_alias_has_one_owner():
    state = {"threads": {"correction": "thread-id"}}
    key = qualify_legacy_thread(state, "Q12", "U-201", "correction")

    assert key == "U-201:correction"
    assert state["threads"] == {"U-201:correction": "thread-id"}
