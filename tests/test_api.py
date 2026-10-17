import json

import pytest
from fastapi.testclient import TestClient

from app.errors import AppError
from app.main import create_app


class Knowledge:
    def info(self): return {'dataset_version':'v1','knowledge_revision':0,'analysis_date':'2026-10-16','counts':{'assets':1}}
    def users(self): return [{'user_id':'A','name':'Alice'}, {'user_id':'B','name':'Bob'}]
    def schema_text(self): return 'assets(asset_id)'
    def rules_text(self): return 'OM-T200#9.3: 15 C'
    def query_shared(self, sql, params=None):
        return {'columns':[{'name':'asset_id','type':'string','label':'Well','unit':None}], 'rows':[{'asset_id':'WELL-0001'}], 'evidence_refs':['INS-0001-0203'], 'complete':True, 'truncated':False,'limitations':[], 'analysis_date':'2026-10-16','dataset_version':'v1','knowledge_revision':0}
    def get_shared_evidence(self, refs):
        if refs != ['INS-0001-0203']: raise AppError('not_found','Evidence not found',404)
        return [{'id':'INS-0001-0203','kind':'inspection','title':'Inspection','content':{'asset_id':'WELL-0001'}}]


class Model:
    model='fixture-model'; configured=True
    def __init__(self): self.calls=0
    def complete(self, messages, tools, **kwargs):
        self.calls += 1
        if self.calls % 2:
            return {'message':{'role':'assistant','tool_calls':[{'id':'query','type':'function','function':{'name':'run_sql','arguments':json.dumps({'sql':'SELECT asset_id FROM assets'})}}]}}
        result=json.loads(messages[-1]['content'])
        return {'message':{'content':json.dumps({'answer':'The selected well is WELL-0001.','ui':'root = AnswerLayout([card])\ncard = ResultCard('+json.dumps(result['result_id'])+', "Well", ["asset_id"])','citation_refs':['INS-0001-0203'],'conflicts':[],'limitations':[],'entity_ids':['WELL-0001']})}}


@pytest.fixture
def client(tmp_path):
    model=Model()
    with TestClient(create_app(knowledge=Knowledge(),memory_path=tmp_path/'memory.sqlite',provider=model)) as c:
        yield c,model


def test_api_threads_chat_cache_and_result_ownership(client):
    c,model=client
    assert c.get('/api/health').json()['ready'] is True
    assert c.post('/api/threads',json={'user_id':'unknown'}).status_code == 404
    t=c.post('/api/threads',json={'user_id':'A'}).json()['thread_id']
    body={'request_id':'request1','user_id':'A','thread_id':t,'text':'Show one well'}
    response=c.post('/api/chat',json=body)
    assert response.status_code == 200, response.text
    answer=response.json();assert next(iter(answer['results'].values()))['rows']==[{'asset_id':'WELL-0001'}]
    assert c.post('/api/chat',json=body).json()==answer
    assert model.calls==2
    assert len(c.get(f'/api/threads/{t}/messages',params={'user_id':'A'}).json()['messages'])==2
    assert c.get(f'/api/threads/{t}/messages',params={'user_id':'B'}).status_code == 404
    rid=next(iter(answer['results']))
    assert c.get(f'/api/results/{rid}',params={'user_id':'B'}).status_code == 404
    assert c.get(f'/api/evidence/{rid}',params={'user_id':'B'}).status_code == 404
    assert c.get(f'/api/results/{rid}',params={'user_id':'A'}).status_code == 200
    mid=answer['message_id']
    assert c.get(f'/api/evidence/{mid}',params={'user_id':'A'}).status_code == 200
    assert c.get(f'/api/evidence/{mid}',params={'user_id':'B'}).status_code == 404


def test_provider_failure_is_clear_and_retry_does_not_duplicate_user_turn(tmp_path):
    class Failing:
        model='missing';configured=False
        def complete(self,*args,**kwargs):raise AppError('provider_error','No API key configured',503)
    with TestClient(create_app(knowledge=Knowledge(),memory_path=tmp_path/'memory.sqlite',provider=Failing())) as c:
        t=c.post('/api/threads',json={'user_id':'A'}).json()['thread_id']
        body={'request_id':'q','user_id':'A','thread_id':t,'text':'Hello'}
        for _ in range(2): assert c.post('/api/chat',json=body).status_code==503
        assert len(c.get(f'/api/threads/{t}/messages',params={'user_id':'A'}).json()['messages'])==1


def test_timeout_after_tool_round_exposes_safe_metadata_and_same_id_retry_keeps_one_user_turn(tmp_path):
    class TimeoutThenSuccess:
        model='inference-router'; configured=True
        def __init__(self): self.calls=0
        def complete(self,messages,tools,**kwargs):
            self.calls+=1
            if self.calls==1:
                return {'message':{'role':'assistant','tool_calls':[{'id':'query','type':'function','function':{'name':'run_sql','arguments':json.dumps({'sql':'SELECT asset_id FROM assets'})}}]},'model':'query-model','usage':{'prompt_tokens':11}}
            if self.calls==2:
                error=AppError('timeout','Model provider timed out; the request can be retried.',504)
                error.private_response='secret provider payload'
                raise error
            return {'message':{'content':json.dumps({'answer':'WELL-0001 is supported by the inspection record.','ui':None,'citation_refs':['INS-0001-0203'],'conflicts':[],'limitations':[],'entity_ids':['WELL-0001']})},'model':'answer-model','usage':{'completion_tokens':5}}

    model=TimeoutThenSuccess()
    with TestClient(create_app(knowledge=Knowledge(),memory_path=tmp_path/'memory.sqlite',provider=model)) as c:
        thread=c.post('/api/threads',json={'user_id':'A'}).json()['thread_id']
        body={'request_id':'timeout-retry','user_id':'A','thread_id':thread,'text':'Show the selected well'}
        failed=c.post('/api/chat',json=body)
        assert failed.status_code==504
        payload=failed.json()
        assert payload['error']=={'code':'timeout','message':'Model provider timed out; the request can be retried.'}
        assert payload['evaluation_metadata']['served_models']==['query-model']
        assert payload['evaluation_metadata']['usage']=={'prompt_tokens':11}
        assert payload['evaluation_metadata']['latency_ms']>=0
        assert 'private_response' not in payload and 'secret provider payload' not in failed.text

        retried=c.post('/api/chat',json=body)
        assert retried.status_code==200, retried.text
        assert model.calls==3
        messages=c.get(f'/api/threads/{thread}/messages',params={'user_id':'A'}).json()['messages']
        assert [m['role'] for m in messages]==['user','assistant']


def test_blank_message_is_rejected(client):
    c,_=client
    assert c.post('/api/chat',json={'request_id':'q','user_id':'A','thread_id':'t','text':'   '}).status_code==422
