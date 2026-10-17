"""Real sample data through the complete HTTP/tool/result path; model is scripted."""
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.load import load_dataset
from app.main import create_app
from app.store import KnowledgeStore


class SampleModel:
    model='scripted-real-data';configured=True

    def complete(self,messages,tools,**kwargs):
        if messages[-1]['role']=='user':
            return {'message':{'tool_calls':[{'id':'latest','type':'function','function':{'name':'run_sql','arguments':json.dumps({'sql':'SELECT inspection_id, asset_id, producing FROM latest_inspections WHERE asset_id = ?', 'params':['WELL-0001']})}}]}}
        result=json.loads(messages[-1]['content'])
        row=result['rows'][0]
        return {'message':{'content':json.dumps({'answer':f"WELL-0001 producing: {row['producing']}",'components':[{'id':'status','type':'card','title':'Latest inspection','result_id':result['result_id'],'mapping':{'fields':['asset_id','producing']}}],'citation_refs':[row['inspection_id'],'OM-T200#9.3'],'entity_ids':['WELL-0001']})}}


def test_real_sample_http_query_sources_and_private_recall(tmp_path):
    source=Path(__file__).resolve().parents[1]/'dataset/sample-data'
    shared=tmp_path/'knowledge.sqlite'
    load_dataset(source,shared)
    knowledge=KnowledgeStore(shared,analysis_date="2026-10-17")
    with TestClient(create_app(knowledge=knowledge,memory_path=tmp_path/'memory.sqlite',provider=SampleModel(),analysis_date="2026-10-17")) as client:
        users=client.get('/api/users').json()['users']
        owner,other=users[0]['user_id'],users[1]['user_id']
        thread=client.post('/api/threads',json={'user_id':owner}).json()['thread_id']
        response=client.post('/api/chat',json={'user_id':owner,'thread_id':thread,'request_id':'real-data','text':'Show the latest production state for WELL-0001.'})
        assert response.status_code==200,response.text
        answer=response.json()
        assert answer['analysis_date']=='2026-10-17'
        assert answer['status']=='complete',answer
        expected=knowledge.query_shared("SELECT producing FROM latest_inspections WHERE asset_id='WELL-0001'")['rows'][0]['producing']
        assert answer['components'][0]['data']['rows'][0]['producing']==expected
        for citation in answer['citations']:
            assert client.get('/api/evidence/'+citation['id'].replace('#','%23'),params={'user_id':owner}).status_code==200
        new_thread=client.post('/api/threads',json={'user_id':owner}).json()['thread_id']
        context=client.app.state.memory.load_context(owner,new_thread)
        assert 'WELL-0001' in context['entity_ids']
        other_thread=client.post('/api/threads',json={'user_id':other}).json()['thread_id']
        assert client.app.state.memory.load_context(other,other_thread)['entity_ids']==[]
        assert client.get('/api/evidence/'+answer['message_id'],params={'user_id':other}).status_code==404
