"""One OpenAI-compatible chat adapter; no credentials are stored or returned."""
import os
from urllib.parse import urlparse

import httpx

from app.errors import AppError


def _digitalocean_403_hint(response):
    """Map explicit provider wording to safe categories without echoing its body."""
    try:
        body = response.text.lower()
    except Exception:
        body = ""
    if any(term in body for term in ("invalid api key", "invalid access key", "expired api key", "revoked api key")):
        return " DigitalOcean rejected the access key; verify that it is active and is a model access key or personal access token."
    if any(term in body for term in ("model scope", "not authorized for model", "not permitted to use model", "no access to model", "model is not allowed")):
        return " The key may not be scoped to this model; check its model list in DigitalOcean Model Access Keys."
    if "vpc" in body and any(term in body for term in ("restrict", "network", "source")):
        return " The key may be restricted to a different VPC; check its network restriction in DigitalOcean Model Access Keys."
    if any(term in body for term in ("insufficient balance", "insufficient inference balance", "no inference balance", "insufficient credits", "balance is empty")):
        return " DigitalOcean reports no available inference balance; check promotional credits and prepaid balances."
    return " DigitalOcean denied the request. Check key status, model scope, VPC restriction, and inference balance."


class CompatibleProvider:
    def __init__(self, model=None, base_url=None, api_key=None, *, transport=None):
        self.model = model or os.getenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.transport = transport
        url = urlparse(self.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise AppError("invalid_request", "LLM_BASE_URL must be an HTTP(S) API base URL without credentials/query parameters.")
        do_endpoint = url.hostname == "inference.do-ai.run"
        self.api_key = api_key if api_key is not None else (
            os.getenv("LLM_API_KEY") or
            (os.getenv("GRADIENT_MODEL_ACCESS_KEY", "") if do_endpoint else os.getenv("OPENROUTER_API_KEY", ""))
        )
        self.local = url.hostname in {"localhost", "127.0.0.1", "::1"}
        self.digitalocean = do_endpoint

    @property
    def configured(self):
        return bool(self.model and (self.api_key or self.local))

    def complete(self, messages, tools, *, timeout=45.0, max_tokens=4096):
        if not self.configured:
            raise AppError("provider_error", "No API key is configured. Set GRADIENT_MODEL_ACCESS_KEY for DigitalOcean, LLM_API_KEY, or the provider-specific key.", 503)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(timeout, connect=min(timeout, 10))) as client:
                payload = {"model": self.model, "messages": messages, "tools": tools, "stream": False}
                payload["max_completion_tokens" if self.digitalocean else "max_tokens"] = max_tokens
                response = client.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
            message = data["choices"][0]["message"]
            if not isinstance(message, dict) or not (message.get("content") or message.get("tool_calls")):
                raise ValueError("Empty provider response")
            if message.get("content") is not None and not isinstance(message["content"], str):
                raise ValueError("Invalid provider text")
            if message.get("tool_calls") is not None:
                if not isinstance(message["tool_calls"], list):
                    raise ValueError("Invalid tool calls")
                for call in message["tool_calls"]:
                    if not isinstance(call, dict) or not isinstance(call.get("id"), str) or call.get("type") != "function" or not isinstance(call.get("function"), dict) or not isinstance(call["function"].get("name"), str) or not isinstance(call["function"].get("arguments"), str):
                        raise ValueError("Malformed provider tool call")
            return {"message": message, "usage": data.get("usage", {})}
        except httpx.TimeoutException as exc:
            raise AppError("timeout", "Model provider timed out; the request can be retried.", 504) from exc
        except httpx.HTTPStatusError as exc:
            code = exc.response.status_code
            if self.digitalocean and code == 403:
                hint = _digitalocean_403_hint(exc.response)
            else:
                hint = " Check provider credits/rate limits." if code in {402, 429} else " Check the configured model and credentials."
            raise AppError("provider_error", f"Model provider returned HTTP {code}.{hint}", 502) from exc
        except (httpx.RequestError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise AppError("provider_error", "Model provider returned an invalid response or could not be reached.", 502) from exc
