import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import check_provider


def test_smoke_checks_bounded_function_roundtrip_without_printing_output(monkeypatch):
    calls=[]
    class FakeProvider:
        model='mock';configured=True
        def complete(self,messages,tools,**kwargs):
            calls.append((list(messages),kwargs))
            if len(calls)==1:
                return {'message':{'role':'assistant','tool_calls':[{'id':'add','type':'function','function':{'name':'add_numbers','arguments':json.dumps({'a':19,'b':23})}}]},'usage':{'total_tokens':10},'model':'served-model-1'}
            assert json.loads(messages[-1]['content'])=={'sum':42}
            return {'message':{'content':'42'},'usage':{'total_tokens':12},'model':'served-model-2'}
    monkeypatch.setattr(check_provider,'CompatibleProvider',FakeProvider)
    monkeypatch.setattr(check_provider,'load_dotenv',lambda *a,**k:None)
    assert check_provider.run()=={'model':'mock','served_models':['served-model-1','served-model-2'],'tool_calls':1,'roundtrip':'ok','usage':22}
    assert len(calls)==2
    assert all(options['max_tokens']==256 for _,options in calls)


def test_smoke_rejects_unrequested_tools_before_continuing(monkeypatch):
    class BadProvider:
        configured=True
        def complete(self,*a,**kw):
            return {'message':{'tool_calls':[{'id':'x','function':{'name':'run_shell','arguments':'{}'}}]}}
    monkeypatch.setattr(check_provider,'CompatibleProvider',BadProvider)
    monkeypatch.setattr(check_provider,'load_dotenv',lambda *a,**k:None)
    with pytest.raises(RuntimeError,match='unsupported function'):
        check_provider.run()


@pytest.mark.parametrize(("status", "body", "expected"), [
    (200, {"data": [{"id": "model"}]}, {"http_status": 200, "model_visible": True, "status": "ok"}),
    (200, {"data": [{"id": "other"}]}, {"http_status": 200, "model_visible": False, "status": "ok"}),
    (403, {"error": {"message": "private provider detail"}}, {"http_status": 403, "model_visible": None, "status": "forbidden", "guidance": "DigitalOcean denied the request. Check account tier, key status, model scope, VPC restriction, and inference balance.", "checks": ["account tier", "key status", "model scope", "VPC restriction", "inference balance"]}),
])
def test_diagnostic_only_checks_catalog_and_never_returns_body(monkeypatch, status, body, expected):
    calls = []
    class FakeProvider:
        model = "model"
        base_url = "https://inference.do-ai.run/v1"
        api_key = "private-key"
        configured = True
        digitalocean = True
    class FakeResponse:
        status_code = status
        is_success = status < 400
        def json(self):
            return body
    def get(url, **kwargs):
        calls.append((url, kwargs))
        return FakeResponse()
    monkeypatch.setattr(check_provider, "CompatibleProvider", FakeProvider)
    monkeypatch.setattr(check_provider, "load_dotenv", lambda *a, **k: None)
    monkeypatch.setattr(check_provider.httpx, "get", get)
    assert check_provider.run(diagnose_only=True) == expected
    assert len(calls) == 1
    assert calls[0][0] == "https://inference.do-ai.run/v1/models"
    assert calls[0][1]["headers"] == {"Authorization": "Bearer private-key"}
    assert "private provider detail" not in str(expected)


def test_direct_script_imports_from_outside_project_and_missing_key_is_safe(tmp_path):
    script=Path(check_provider.__file__).resolve()
    env={**os.environ,'LLM_API_KEY':'','GRADIENT_MODEL_ACCESS_KEY':'','OPENROUTER_API_KEY':'','LLM_BASE_URL':'https://inference.do-ai.run/v1','LLM_MODEL':'mock'}
    result=subprocess.run([sys.executable,str(script)],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode==1
    assert result.stdout==''
    assert 'No provider key is configured' in result.stderr
    assert 'Traceback' not in result.stderr
