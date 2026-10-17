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
                return {'message':{'role':'assistant','tool_calls':[{'id':'add','type':'function','function':{'name':'add_numbers','arguments':json.dumps({'a':19,'b':23})}}]},'usage':{'total_tokens':10}}
            assert json.loads(messages[-1]['content'])=={'sum':42}
            return {'message':{'content':'42'},'usage':{'total_tokens':12}}
    monkeypatch.setattr(check_provider,'CompatibleProvider',FakeProvider)
    monkeypatch.setattr(check_provider,'load_dotenv',lambda *a,**k:None)
    assert check_provider.run()=={'model':'mock','tool_calls':1,'roundtrip':'ok','usage':22}
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


def test_direct_script_imports_from_outside_project_and_missing_key_is_safe(tmp_path):
    script=Path(check_provider.__file__).resolve()
    env={**os.environ,'LLM_API_KEY':'','GRADIENT_MODEL_ACCESS_KEY':'','OPENROUTER_API_KEY':'','LLM_BASE_URL':'https://inference.do-ai.run/v1','LLM_MODEL':'mock'}
    result=subprocess.run([sys.executable,str(script)],cwd=tmp_path,env=env,capture_output=True,text=True,timeout=10)
    assert result.returncode==1
    assert result.stdout==''
    assert 'No provider key is configured' in result.stderr
    assert 'Traceback' not in result.stderr
