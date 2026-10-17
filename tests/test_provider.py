import httpx
import pytest

from app.errors import AppError
from app.provider import CompatibleProvider


def test_provider_preserves_tools_and_uses_configured_endpoint():
    seen = []
    def respond(request):
        seen.append(request)
        return httpx.Response(200, json={"choices": [{"message": {"role": "assistant", "content": "ok"}}], "usage": {"total_tokens": 12}})
    provider = CompatibleProvider("test-model", "https://example.test/v1", "test-key", transport=httpx.MockTransport(respond))
    result = provider.complete([{"role": "user", "content": "hello"}], [{"type": "function", "function": {"name": "lookup"}}])
    assert str(seen[0].url) == "https://example.test/v1/chat/completions"
    assert result["message"]["content"] == "ok"
    assert result["usage"]["total_tokens"] == 12
    assert b'"tools"' in seen[0].content


def test_provider_rejects_missing_remote_credentials_before_network():
    with pytest.raises(AppError, match="API key"):
        CompatibleProvider("test-model", "https://example.test/v1", "").complete([], [])


def test_provider_errors_do_not_echo_credentials_or_response_body():
    provider = CompatibleProvider("test-model", "https://example.test/v1", "secret-key", transport=httpx.MockTransport(lambda _: httpx.Response(401, text="secret-key")))
    with pytest.raises(AppError) as caught:
        provider.complete([], [])
    assert caught.value.code == "provider_error"
    assert "secret-key" not in str(caught.value)


def test_local_provider_may_run_without_key():
    provider = CompatibleProvider("local", "http://127.0.0.1:11434/v1", "", transport=httpx.MockTransport(lambda _: httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]})))
    assert provider.complete([], [])["message"]["content"] == "ok"


def test_provider_rejects_malformed_tool_call():
    provider=CompatibleProvider('local','http://localhost:11434/v1','',transport=httpx.MockTransport(lambda _:httpx.Response(200,json={'choices':[{'message':{'tool_calls':[{'type':'function','id':'x','function':{'name':'lookup','arguments':{}}}]}}]})))
    with pytest.raises(AppError,match='invalid response'):
        provider.complete([],[])
