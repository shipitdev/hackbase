"""Explicit, low-budget provider and function-calling smoke check."""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.errors import AppError
from app.provider import CompatibleProvider


def run():
    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False, interpolate=False)
    provider = CompatibleProvider()
    if not provider.configured:
        raise AppError("provider_error", "No provider key is configured.", 503)
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
        print(json.dumps(run()))
    except AppError as exc:
        print(f"Provider check failed: {exc.code}: {exc.message}", file=sys.stderr)
        raise SystemExit(1)
    except Exception as exc:
        print(f"Provider check failed: {type(exc).__name__}", file=sys.stderr)
        raise SystemExit(1)
