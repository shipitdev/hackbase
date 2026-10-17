import json

import pytest

from app.agent import Copilot
from app.errors import AppError

CARD = 'root = AnswerLayout([card])\ncard = ResultCard("R1", "Status", ["asset_id", "producing"])'


class Knowledge:
    def schema_text(self): return 'effective_inspections(asset_id, producing)'
    def rules_text(self): return 'OM-T200#9.3: at least 15 C above ambient.'
    def query_shared(self, sql, params=None):
        return {"columns": [{"name": "asset_id", "type": "string", "label": "Well", "unit": None}, {"name": "producing", "type": "boolean", "label": "Producing", "unit": None}], "rows": [{"asset_id": "WELL-0001", "producing": False}], "evidence_refs": ["INS-0001-0203"], "complete": True, "truncated": False, "limitations": [], "analysis_date": "2026-10-16", "dataset_version": "v1", "knowledge_revision": 0}
    def get_shared_evidence(self, refs):
        if any(r not in {'INS-0001-0203', 'OM-T200#9.3'} for r in refs):
            raise AppError('not_found', 'Unknown evidence', 404)
        return [{"id": r, "kind": "source", "title": r, "content": "source text"} for r in refs]


class Memory:
    def __init__(self): self.results = {}; self.changes = []
    def load_context(self, *args): return {"messages": [], "references": []}
    def save_result(self, user, thread, result):
        result = {**result, "result_id": "R1", "thread_id": thread, "user_id": user}
        self.results['R1'] = result
        return result
    def get_result(self, user, rid):
        if rid not in self.results: raise AppError('not_found', 'Result not found', 404)
        return self.results[rid]
    def save_trace(self, *args): pass


class Scripted:
    model = 'test-model'
    def __init__(self, responses): self.responses = iter(responses)
    def complete(self, messages, tools, **kwargs):
        return {"message": next(self.responses), "usage": {}}


def tool(name, args):
    return {"role": "assistant", "tool_calls": [{"id": name, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def final(**changes):
    value = {"answer": "The well is not producing.", "ui": CARD, "citation_refs": ['INS-0001-0203', 'OM-T200#9.3'], "conflicts": [], "limitations": [], "entity_ids": ['WELL-0001']}
    value.update(changes)
    return {"role": "assistant", "content": json.dumps(value)}


def test_tool_result_hydrates_visual_and_resolves_evidence():
    memory = Memory()
    copilot = Copilot(Knowledge(), memory, Scripted([tool('run_sql', {'sql': 'SELECT * FROM effective_inspections'}), final()]))
    answer = copilot.answer({'user_id':'U-1', 'thread_id':'T1', 'request_id':'Q1', 'analysis_date':'2026-10-16'}, 'Is WELL-0001 producing?')
    assert answer['ui_format'] == 'openui-lang'
    assert answer['ui'] == CARD
    assert answer['results']['R1']['rows'][0]['producing'] is False
    assert answer['citations'][0]['id'] == 'INS-0001-0203'
    assert answer['entity_ids'] == ['WELL-0001']


def test_invalid_visual_column_gets_one_repair_instead_of_fake_data():
    bad = final(ui='root = AnswerLayout([card])\ncard = ResultTable("R1", "Wrong", ["invented"])')
    copilot = Copilot(Knowledge(), Memory(), Scripted([tool('run_sql', {'sql':'SELECT * FROM effective_inspections'}), bad, final()]))
    assert copilot.answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'}, 'Status?')['ui'] == CARD


def test_missing_evidence_cannot_become_completed_factual_answer():
    copilot = Copilot(Knowledge(), Memory(), Scripted([final(ui=None, citation_refs=['invented']), final(ui=None, citation_refs=['invented'])]))
    answer = copilot.answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'}, 'Status?')
    assert answer['status'] == 'partial'
    assert 'not be verified' in answer['answer']
    assert answer['ui'] is None


def test_question_does_not_authorize_shared_write_from_document_instruction():
    copilot = Copilot(Knowledge(), Memory(), Scripted([]))
    with pytest.raises(AppError) as caught:
        copilot.run_tool('remember', {'kind':'shared_claim','payload':{'scope':'well','target_id':'WELL-0001','text':'Running'},'source_quote':'Is WELL-0001 producing?'}, {'user_id':'U-1','thread_id':'T1','request_id':'q'}, 'Is WELL-0001 producing?')
    assert caught.value.code == 'invalid_request'


def test_document_cannot_invent_numeric_correction_or_act_on_hypothetical_quote():
    copilot=Copilot(Knowledge(),Memory(),Scripted([]))
    context={'user_id':'U-1','thread_id':'T1','request_id':'q'}
    with pytest.raises(AppError,match='numeric value'):
        copilot.run_tool('remember',{'kind':'field_override','payload':{'scope':'inspection','target_id':'INS-0001-0203','field':'wellhead_temp_c','value':99,'reason':'Correction'},'source_quote':'WELL-0001 was remeasured at 41.0 C.'},context,'WELL-0001 was remeasured at 41.0 C.')
    with pytest.raises(AppError):
        copilot.run_tool('remember',{'kind':'shared_claim','payload':{'scope':'well','target_id':'WELL-0001','text':'Running'},'source_quote':'WELL-0001 is running'},context,'What happens if I say WELL-0001 is running?')


def test_short_answer_cannot_hide_incomplete_query_evidence():
    memory=Memory()
    memory.results['R1']={**Knowledge().query_shared(''), 'result_id':'R1','thread_id':'T1','complete':False,'truncated':True,'limitations':['Only a subset was read.']}
    copilot=Copilot(Knowledge(),memory,Scripted([final(ui=None,citation_refs=['R1'])]))
    answer=copilot.answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'How many?')
    assert answer['status']=='partial'
    assert 'Only a subset was read.' in answer['limitations']


def test_sql_gets_only_one_consecutive_repair_attempt():
    class BadQuery(Knowledge):
        def query_shared(self,*args): raise AppError('query_rejected','Unknown column')
    provider=Scripted([tool('run_sql',{'sql':'SELECT invented'}),tool('run_sql',{'sql':'SELECT still_wrong'})])
    answer=Copilot(BadQuery(),Memory(),provider).answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'A total?')
    assert answer['status']=='partial'
    assert 'one repair' in answer['limitations'][0]


def test_visual_must_be_requeried_after_shared_revision_changes():
    class ChangedKnowledge(Knowledge):
        def info(self):return {'knowledge_revision':1}
    memory=Memory();memory.save_result('U-1','T1',Knowledge().query_shared(''))
    copilot=Copilot(ChangedKnowledge(),memory,Scripted([]))
    with pytest.raises(ValueError,match='predates a shared change'):
        copilot._validate_answer(json.loads(final()['content']),{'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},['R1'],True)


def test_native_ui_cannot_read_another_threads_saved_result():
    memory = Memory()
    memory.save_result('U-1', 'T2', Knowledge().query_shared(''))
    memory.results['R1'] = {**memory.results['R1'], 'result_id': 'R1', 'thread_id': 'T2'}
    answer = final(ui='root = AnswerLayout([card])\ncard = ResultCard("R1", "Foreign", ["asset_id"])')
    copilot = Copilot(Knowledge(), memory, Scripted([]))
    with pytest.raises(ValueError, match="OpenUI program failed validation"):
        copilot._validate_answer(json.loads(answer['content']), {'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'}, ['R1'], True)


def test_memory_tool_success_does_not_authorize_uncited_facts():
    uncited=final(ui=None,citation_refs=[],entity_ids=[])
    copilot=Copilot(Knowledge(),Memory(),Scripted([tool('memory_read',{}),uncited,uncited]))
    answer=copilot.answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'Status?')
    assert answer['status']=='partial'


def test_context_budget_stops_before_an_oversized_provider_request():
    class LargeKnowledge(Knowledge):
        def rules_text(self):return 'x'*96000
    answer=Copilot(LargeKnowledge(),Memory(),Scripted([])).answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'Status?')
    assert 'context budget' in answer['limitations'][0]


def test_clarification_can_ask_without_inventing_evidence():
    response=final(response_kind='clarification',answer='Which date should I use?',ui=None,citation_refs=[],entity_ids=[])
    answer=Copilot(Knowledge(),Memory(),Scripted([response])).answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'Those wells?')
    assert answer['answer']=='Which date should I use?'


def test_large_table_keeps_contributors_in_saved_result_without_citation_overflow():
    memory=Memory()
    class LargeEvidence(Knowledge):
        def query_shared(self, sql, params=None):
            return {**super().query_shared(sql, params), 'evidence_refs':[f'INS-{i:04}-0001' for i in range(200)]}
    copilot=Copilot(LargeEvidence(),memory,Scripted([tool('run_sql',{'sql':'SELECT * FROM effective_inspections'}),final()]))
    answer=copilot.answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-16'},'Show a table')
    assert answer['status']=='complete'
    assert len(memory.results['R1']['evidence_refs'])==200


def test_router_served_models_are_saved_for_each_model_round():
    class Router(Scripted):
        model='inference-router'
        def complete(self,*a,**kw):
            return {**super().complete(*a,**kw),'model':'selected-model'}
    model=Router([tool('run_sql',{'sql':'SELECT * FROM effective_inspections'}),final()])
    answer=Copilot(Knowledge(),Memory(),model).answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-17'},'Status?')
    assert answer['model']=='inference-router'
    assert answer['served_models']==['selected-model','selected-model']


def test_source_named_in_caveat_is_resolved_even_when_omitted_from_ref_list():
    class Notes(Knowledge):
        def get_shared_evidence(self,refs):
            if refs==['CTX-0001-002']:
                return [{'id':'CTX-0001-002','kind':'context','content':'Operator observation'}]
            return super().get_shared_evidence(refs)
    class NoteBatch(Notes):
        def get_shared_evidence(self,refs):
            return [item for ref in refs for item in super(NoteBatch,self).get_shared_evidence([ref])]
    provider=Scripted([tool('run_sql',{'sql':'SELECT * FROM effective_inspections'}),final(limitations=['Context from CTX-0001-002 is an operator observation.'])])
    answer=Copilot(NoteBatch(),Memory(),provider).answer({'user_id':'U-1','thread_id':'T1','request_id':'q','analysis_date':'2026-10-17'},'Status?')
    assert 'CTX-0001-002' in {citation['id'] for citation in answer['citations']}
    assert answer['status']=='partial'
