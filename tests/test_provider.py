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


def test_digitalocean_uses_gradient_key_and_completion_token_parameter(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "do-key")
    seen = []
    provider = CompatibleProvider("deepseek-v4.1-flash", "https://inference.do-ai.run/v1", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    ))
    provider.complete([{"role": "user", "content": "hi"}], [{"type": "function"}], max_tokens=256)
    assert seen[0].headers["authorization"] == "Bearer do-key"
    assert b'"max_completion_tokens":256' in seen[0].content
    assert b'"max_tokens"' not in seen[0].content
    assert b'"tools"' in seen[0].content


@pytest.mark.parametrize("preference", ["balanced", "budget", "quality"])
def test_digitalocean_router_sends_validated_preference_and_reports_served_model(monkeypatch, preference):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "do-key")
    monkeypatch.setenv("LLM_ROUTING_PREFERENCE", preference)
    seen = []
    provider = CompatibleProvider("inference-router", "https://inference.do-ai.run/v1", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"model": "openai-gpt-oss-120b", "choices": [{"message": {"content": "ok"}}]}))
    ))
    result = provider.complete([{"role": "user", "content": "hi"}], [{"type": "function"}], max_tokens=256)
    assert result["model"] == "openai-gpt-oss-120b"
    assert b'"model":"inference-router"' in seen[0].content
    assert f'"routing_preference":"{preference}"'.encode() in seen[0].content
    assert b'"max_completion_tokens":256' in seen[0].content
    assert b'"tools"' in seen[0].content


def test_digitalocean_router_defaults_to_budget_and_rejects_invalid_preference(monkeypatch):
    monkeypatch.delenv("LLM_ROUTING_PREFERENCE", raising=False)
    seen = []
    provider = CompatibleProvider("inference-router", "https://inference.do-ai.run/v1", "key", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    ))
    provider.complete([], [])
    assert provider.routing_preference == "budget"
    assert b'"routing_preference":"budget"' in seen[0].content
    monkeypatch.setenv("LLM_ROUTING_PREFERENCE", "cheapest")
    with pytest.raises(AppError, match="LLM_ROUTING_PREFERENCE"):
        CompatibleProvider("inference-router", "https://inference.do-ai.run/v1", "key")


def test_router_preference_is_ignored_by_other_provider(monkeypatch):
    monkeypatch.setenv("LLM_ROUTING_PREFERENCE", "quality")
    seen = []
    provider = CompatibleProvider("inference-router", "https://example.test/v1", "key", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    ))
    provider.complete([], [])
    assert b'"routing_preference"' not in seen[0].content


def test_digitalocean_llm_api_key_takes_priority(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "preferred")
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "gradient")
    seen = []
    provider = CompatibleProvider("do-model", "https://inference.do-ai.run/v1", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    ))
    provider.complete([], [])
    assert seen[0].headers["authorization"] == "Bearer preferred"


@pytest.mark.parametrize("status", [401, 402, 429, 500])
def test_digitalocean_errors_are_safe(status, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "secret-do-key")
    provider = CompatibleProvider("model", "https://inference.do-ai.run/v1", transport=httpx.MockTransport(
        lambda _: httpx.Response(status, text="secret-do-key private provider payload")
    ))
    with pytest.raises(AppError) as caught:
        provider.complete([], [])
    assert caught.value.code == "provider_error"
    assert str(status) in str(caught.value)
    assert "secret-do-key" not in str(caught.value)
    assert "private provider payload" not in str(caught.value)


@pytest.mark.parametrize(("body", "hint"), [
    ('{"error":{"message":"key not authorized for model: private-id"}}', "model list in DigitalOcean Model Access Keys"),
    ('{"error":{"message":"key not authorized for router: private-id"}}', "check Inference routers access"),
    ('{"error":{"message":"Model is not available on the current account tier: private-id"}}', "account tier"),
    ('{"error":{"message":"VPC network restriction: private-network"}}', "different VPC"),
    ('{"error":{"message":"invalid api key: private-secret"}}', "access key"),
    ('{"error":{"message":"insufficient inference balance: private-account"}}', "DigitalOcean reports no available inference balance"),
    ('{"error":{"message":"private denial detail"}}', "DigitalOcean denied the request"),
])
def test_digitalocean_403_maps_only_safe_categories(body, hint, monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "secret-do-key")
    provider = CompatibleProvider("model", "https://inference.do-ai.run/v1", transport=httpx.MockTransport(
        lambda _: httpx.Response(403, text=body)
    ))
    with pytest.raises(AppError) as caught:
        provider.complete([], [])
    assert hint in str(caught.value)
    assert "private-" not in str(caught.value)
    assert "secret-do-key" not in str(caught.value)


def test_gradient_key_is_not_used_for_generic_endpoint(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("GRADIENT_MODEL_ACCESS_KEY", "gradient")
    provider = CompatibleProvider("model", "https://example.test/v1", transport=httpx.MockTransport(lambda _: pytest.fail("unexpected request")))
    with pytest.raises(AppError, match="API key"):
        provider.complete([], [])


def test_generic_endpoint_keeps_legacy_max_tokens(monkeypatch):
    seen = []
    provider = CompatibleProvider("model", "https://example.test/v1", "key", transport=httpx.MockTransport(
        lambda request: (seen.append(request) or httpx.Response(200, json={"choices": [{"message": {"content": "ok"}}]}))
    ))
    provider.complete([], [], max_tokens=128)
    assert b'"max_tokens":128' in seen[0].content
    assert b'"max_completion_tokens"' not in seen[0].content


@pytest.mark.parametrize(('failure','message'),[(httpx.ConnectError,'Could not connect'),(httpx.ReadError,'transport failed')])
def test_transport_failures_are_distinct_and_do_not_echo_secrets(failure,message):
    def fail(request):raise failure('private-key private-response',request=request)
    provider=CompatibleProvider('model','https://example.test/v1','private-key',transport=httpx.MockTransport(fail))
    with pytest.raises(AppError) as caught:provider.complete([],[])
    assert message in str(caught.value)
    assert 'private-' not in str(caught.value)
