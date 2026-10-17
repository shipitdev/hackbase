import json
from pathlib import Path

from app.load import load_dataset
from scripts.check_backend_question import run


class ScriptedProvider:
    model = "scripted-q1"
    configured = True

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools, **kwargs):
        self.calls += 1
        if self.calls == 1:
            return {"message": {"tool_calls": [{
                "id": "latest", "type": "function", "function": {
                    "name": "run_sql", "arguments": json.dumps({
                        "sql": "SELECT asset_id, inspection_id, inspected_at, producing, wellhead_temp_c, ambient_temp_c FROM latest_inspections WHERE asset_id=?",
                        "params": ["WELL-0001"],
                    }),
                },
            }]}}
        result = json.loads(messages[-1]["content"])
        row = result["rows"][0]
        return {"message": {"content": json.dumps({
            "answer": f"WELL-0001 is {'producing' if row['producing'] else 'not producing'} based on its latest inspection and T200 rule. Jake's planned shut-in note is relevant.",
            "components": [{"id": "status", "type": "card", "title": "Latest inspection", "result_id": result["result_id"], "mapping": {"fields": ["asset_id", "inspection_id", "inspected_at", "producing"]}}],
            "citation_refs": [row["inspection_id"], "OM-T200#9.3", "CTX-0001-003"],
            "entity_ids": ["WELL-0001"],
        })}, "model": self.model, "usage": {"total_tokens": 12}}


def test_live_question_harness_uses_snapshot_and_validates_saved_card(tmp_path):
    root = Path(__file__).resolve().parents[1]
    database = tmp_path / "shared.sqlite"
    load_dataset(root / "dataset" / "sample-data", database)
    provider = ScriptedProvider()

    outcome = run(database, provider=provider)

    assert outcome["status"] == "pass"
    assert outcome["state"] == "not producing"
    assert outcome["inspection_id"] == "INS-0001-0203"
    assert "OM-T200#9.3" in outcome["citations"]
    assert provider.calls == 2


def test_status_acceptance_allows_generated_card_plus_supporting_table():
    from scripts.check_backend_question import _check_answer
    expected={'asset_id':'WELL-0001','producing':0,'inspection_id':'INS-0001-0203','inspected_at':'2026-10-15'}
    answer={'status':'complete','analysis_date':'2026-10-17','answer':'WELL-0001 is not producing.',
        'components':[{'type':'card','mapping':{'fields':['asset_id','producing']},'result_id':'R1','data':{'rows':[{'asset_id':'WELL-0001','producing':0}],'complete':True}}, {'type':'table','result_id':'R2'}],
        'citations':[{'id':ref} for ref in ['INS-0001-0203','OM-T200#9.3','CTX-0001-003','R1']]}
    assert _check_answer(answer,expected)['state']=='not producing'
