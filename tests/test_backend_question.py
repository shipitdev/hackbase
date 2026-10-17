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
                        "sql": "SELECT asset_id, inspection_id, inspected_at, producing, wellhead_temp_c, ambient_temp_c, production_threshold_c FROM latest_inspections WHERE asset_id=?",
                        "params": ["WELL-0001"],
                    }),
                },
            }]}}
        result = json.loads(messages[-1]["content"])
        row = result["rows"][0]
        return {"message": {"content": json.dumps({
            "answer": f"WELL-0001 is {'producing' if row['producing'] else 'not producing'} based on its latest inspection and T200 rule. Jake's planned shut-in note is relevant.",
            "components": [{"id": "status", "type": "card", "title": "Latest inspection", "result_id": result["result_id"], "mapping": {"fields": ["asset_id", "inspection_id", "inspected_at", "wellhead_temp_c", "ambient_temp_c", "production_threshold_c", "producing"]}}],
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
    expected={'asset_id':'WELL-0001','producing':0,'inspection_id':'INS-0001-0203','inspected_at':'2026-10-15T09:45:00Z','wellhead_temp_c':25.6,'ambient_temp_c':22.4,'production_threshold_c':15.0}
    card_row={k:expected[k] for k in ('asset_id','producing','inspection_id','inspected_at','wellhead_temp_c','ambient_temp_c','production_threshold_c')}
    note_row={'note_id':'CTX-0001-003','text':'Work order not yet in the maintenance system.'}
    answer={'status':'partial','analysis_date':'2026-10-17','answer':'WELL-0001 is not producing.',
        'limitations':['No inspection exists after 2026-10-15; status after that date is unknown.', 'The operator note has no work order; the planned job is unverified.'],
        'components':[{'type':'card','mapping':{'fields':list(card_row)},'result_id':'R1','data':{'rows':[card_row],'complete':True,'truncated':False}}, {'type':'table','result_id':'R2','data':{'rows':[note_row],'complete':True,'truncated':False}}],
        'citations':[{'id':'INS-0001-0203','kind':'inspection'}, {'id':'OM-T200#9.3','kind':'document_section'}, {'id':'CTX-0001-003','kind':'context'},
            {'id':'R1','kind':'query_result','content':{'rows':[card_row],'complete':True,'truncated':False}},
            {'id':'R2','kind':'query_result','content':{'rows':[note_row],'complete':True,'truncated':False}}]}
    checked=_check_answer(answer,expected)
    assert checked['state']=='not producing'
    assert checked['status']=='pass_with_limitations'


def test_status_rejects_uncited_counterweight_note():
    import pytest
    from scripts.check_backend_question import CheckFailure, _check_answer
    expected={'asset_id':'WELL-0001','producing':0,'inspection_id':'INS-0001-0203','inspected_at':'2026-10-15T09:45:00Z','wellhead_temp_c':25.6,'ambient_temp_c':22.4,'production_threshold_c':15.0}
    card_row={k:expected[k] for k in ('asset_id','producing','inspection_id','inspected_at','wellhead_temp_c','ambient_temp_c','production_threshold_c')}
    answer={'status':'partial','analysis_date':'2026-10-17','answer':'WELL-0001 is not producing.',
        'limitations':['No inspection exists after 2026-10-15; status after that date is unknown.', 'The operator note has no work order; the planned job is unverified.', 'A Nov 2025 counterweight note describes lower temperatures.'],
        'components':[{'type':'card','mapping':{'fields':list(card_row)},'result_id':'R1','data':{'rows':[card_row],'complete':True,'truncated':False}}],
        'citations':[{'id':'INS-0001-0203','kind':'inspection'}, {'id':'OM-T200#9.3','kind':'document_section'}, {'id':'CTX-0001-003','kind':'context'}, {'id':'R1','kind':'query_result','content':{'rows':[card_row],'complete':True,'truncated':False}}]}
    with pytest.raises(CheckFailure, match='counterweight note without citation CTX-0001-002'):
        _check_answer(answer,expected)
    answer['citations'].append({'id':'CTX-0001-002','kind':'context'})
    assert _check_answer(answer,expected)['status']=='pass_with_limitations'


def test_status_failure_reports_fixed_check_without_echoing_model_text():
    import pytest
    from scripts.check_backend_question import CheckFailure, _check_answer

    expected={'asset_id':'WELL-0001','producing':0,'inspection_id':'INS-0001-0203','inspected_at':'2026-10-15'}
    answer={'status':'complete','analysis_date':'2026-10-17','answer':'WELL-0001 is not producing; private model text'}
    with pytest.raises(CheckFailure, match='answer.components has no status card'):
        _check_answer(answer, expected)


def test_partial_acceptance_does_not_require_one_exact_caveat_phrase():
    from scripts.check_backend_question import _check_answer
    expected={'asset_id':'WELL-0001','producing':0,'inspection_id':'INS-0001-0203','inspected_at':'2026-10-15T09:45:00Z','wellhead_temp_c':25.6,'ambient_temp_c':22.4,'production_threshold_c':15.0}
    card={'type':'card','mapping':{'fields':list(expected)},'result_id':'R1','data':{'rows':[expected],'complete':True,'truncated':False}}
    answer={'status':'partial','analysis_date':'2026-10-17','answer':'WELL-0001 is not producing.',
        'limitations':['Conditions between the latest reading and now are not directly observed.','The work order is not yet in the maintenance system.'],
        'components':[card], 'citations':[{'id':ref} for ref in ['INS-0001-0203','OM-T200#9.3','CTX-0001-003']]+[{'id':'R1','kind':'query_result','content':{'rows':[expected],'complete':True,'truncated':False}}]}
    assert _check_answer(answer,expected)['status']=='pass_with_limitations'
    answer['components'][0]['data']['rows']=[{**expected,'producing':1}]
    import pytest
    from scripts.check_backend_question import CheckFailure
    with pytest.raises(CheckFailure,match='status card row'):_check_answer(answer,expected)
