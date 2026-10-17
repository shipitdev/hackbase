"""Explicit, low-budget provider and function-calling smoke check."""
import json
import sys
from pathlib import Path

import httpx
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import AppError
from app.provider import CompatibleProvider, _digitalocean_403_hint


def diagnose(provider):
    if not provider.digitalocean:
        raise AppError("invalid_request", "--diagnose requires the DigitalOcean inference endpoint.")
    try:
        response = httpx.get(
            f"{provider.base_url}/models",
            headers={"Authorization": f"Bearer {provider.api_key}"},
            timeout=httpx.Timeout(15, connect=8),
        )
    except httpx.TimeoutException:
        return {"status": "timeout", "model_visible": None}
    except httpx.RequestError:
        return {"status": "unreachable", "model_visible": None}

    result = {"http_status": response.status_code, "model_visible": None}
    if response.is_success:
        try:
            models = response.json().get("data")
            if not isinstance(models, list):
                raise ValueError("Invalid model catalog")
            result["model_visible"] = any(
                isinstance(item, dict) and item.get("id") == provider.model for item in models
            )
        except (AttributeError, TypeError, ValueError):
            result["status"] = "invalid_catalog_response"
            return result
        result["status"] = "ok"
    elif response.status_code == 403:
        result["status"] = "forbidden"
        result["guidance"] = _digitalocean_403_hint(response).strip()
        result["checks"] = ["key status", "model scope", "VPC restriction", "inference balance"]
    elif response.status_code == 401:
        result["status"] = "authentication_rejected"
    elif response.status_code == 402:
        result["status"] = "inference_access_suspended_or_balance_required"
    else:
        result["status"] = "http_error"
    return result


def run(*, diagnose_only=False):
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False, interpolate=False)
    provider = CompatibleProvider()
    if not provider.configured:
        raise AppError("provider_error", "No provider key is configured.", 503)
    if diagnose_only:
        return diagnose(provider)
    messages = [
        {"role": "system", "content": "Call add_numbers exactly once using 19 and 23, then report the sum."},
        {"role": "user", "content": "Run the requested validation."},
    ]
    tools = [{"type": "function", "function": {
        "name": "add_numbers", "description": "Add two numbers for a connectivity check.",
        "parameters": {"type": "object", "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}}, "required": ["a", "b"], "additionalProperties": False},
    }}]
    first_result = provider.complete(messages, tools, max_tokens=256)
    first = first_result["message"]
    calls = first.get("tool_calls")
    if not isinstance(calls, list) or len(calls) != 1:
        raise RuntimeError("Provider did not return a supported function call.")
    messages.append({key: first[key] for key in ("role", "content", "tool_calls", "reasoning_details") if key in first})
    for call in calls:
        if call["function"]["name"] != "add_numbers":
            raise RuntimeError("Provider returned an unsupported function name.")
        try:
            args = json.loads(call["function"]["arguments"])
        except (TypeError, json.JSONDecodeError) as exc:
            raise RuntimeError("Provider returned invalid function arguments.") from exc
        if not isinstance(args, dict) or set(args) != {"a", "b"} or any(type(args[k]) is not int or abs(args[k]) > 1_000_000 for k in ("a", "b")):
            raise RuntimeError("Provider returned invalid function arguments.")
        if args != {"a": 19, "b": 23}:
            raise RuntimeError("Provider did not use the requested function arguments.")
        if (args["a"], args["b"]) != (19, 23):
            raise RuntimeError("Provider returned unexpected function arguments.")
        value = args["a"] + args["b"]
        messages.append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps({"sum": value})})
    final_result = provider.complete(messages, tools, max_tokens=256)
    final = final_result["message"]
    if not isinstance(final.get("content"), str) or not final["content"].strip() or final.get("tool_calls"):
        raise RuntimeError("Provider did not finish after the function result.")
    usage_values = [result.get("usage", {}).get("total_tokens") for result in (first_result, final_result)]
    usage = sum(value for value in usage_values if type(value) is int) if any(type(value) is int for value in usage_values) else None
    # Usage fields are safe metadata; model text, headers, and response bodies stay private.
    return {"model": provider.model, "tool_calls": len(calls), "roundtrip": "ok", "usage": usage}


if __name__ == "__main__":
    try:
        if sys.argv[1:] not in ([], ["--diagnose"]):
            raise AppError("invalid_request", "Usage: python3 scripts/check_provider.py [--diagnose]")
        result = run(diagnose_only=sys.argv[1:] == ["--diagnose"])
        print(json.dumps(result))
        if sys.argv[1:] == ["--diagnose"] and (result.get("status") != "ok" or not result.get("model_visible")):
            raise SystemExit(1)
    except AppError as exc:
        print(f"Provider check failed: {exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Provider check failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
