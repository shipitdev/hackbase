"""One OpenAI-compatible chat adapter; no credentials are stored or returned."""
import os
from urllib.parse import urlparse

import httpx

from app.errors import AppError


class CompatibleProvider:
    def __init__(self, model=None, base_url=None, api_key=None, *, transport=None):
        self.model = model or os.getenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")
        self.base_url = (base_url or os.getenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        self.api_key = api_key if api_key is not None else os.getenv("LLM_API_KEY", os.getenv("OPENROUTER_API_KEY", ""))
        self.transport = transport
        url = urlparse(self.base_url)
        if url.scheme not in {"http", "https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise AppError("invalid_request", "LLM_BASE_URL must be an HTTP(S) API base URL without credentials/query parameters.")
        self.local = url.hostname in {"localhost", "127.0.0.1", "::1"}

    @property
    def configured(self):
        return bool(self.model and (self.api_key or self.local))

    def complete(self, messages, tools, *, timeout=45.0):
        if not self.configured:
            raise AppError("provider_error", "Set LLM_API_KEY (or OPENROUTER_API_KEY), or configure a local provider. No API key is configured.", 503)
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        try:
            with httpx.Client(transport=self.transport, timeout=httpx.Timeout(timeout, connect=min(timeout, 10))) as client:
                response = client.post(f"{self.base_url}/chat/completions", headers=headers, json={
                    "model": self.model, "messages": messages, "tools": tools, "stream": False, "max_tokens": 4096,
                })
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
            hint = " Check provider credits/rate limits." if code in {402, 429} else " Check the configured model and credentials."
            raise AppError("provider_error", f"Model provider returned HTTP {code}.{hint}", 502) from exc
        except (httpx.RequestError, ValueError, KeyError, IndexError, TypeError) as exc:
            raise AppError("provider_error", "Model provider returned an invalid response or could not be reached.", 502) from exc
