# Worker report: B3 — DigitalOcean serverless inference

**Worker/model/effort:** GPT-6 Luna / high (explicit orchestrator assignment)
**Status:** accepted by Sol
**Interface revision:** backend v1, HTTPX Chat Completions adapter

## Delivered

`app/provider.py` now uses `GRADIENT_MODEL_ACCESS_KEY` only for the DigitalOcean inference host, keeps `LLM_API_KEY` first priority and preserves the generic `OPENROUTER_API_KEY` path. DigitalOcean requests use `max_completion_tokens`; the existing generic provider retains `max_tokens`. The optional token limit lets the explicit `scripts/check_provider.py` smoke check cap each of two model requests at 256 tokens. It accepts one expected call to a bounded local addition tool and prints metadata only. Provider tests cover auth precedence, URL, model/tools, token parameter, missing keys and safe errors.

Official docs confirm `/v1/models`, `POST /v1/chat/completions`, and the `max_completion_tokens` parameter: [endpoints](https://docs.digitalocean.com/products/inference/how-to/si-endpoints/), [Chat Completions](https://docs.digitalocean.com/products/inference/how-to/use-chat-completions-api/). The tentative model ID `qwen3.5-397b-a17b` is exact and priced at $0.55/$3.50 per million input/output tokens; `deepseek-v4.1-flash` is exact and priced at $0.30/$1.20. The catalog does not list function calling for either. For this SQL/tool app, recommend `anthropic-claude-5.5-haiku`: the catalog explicitly lists tool calling, and pricing is $0.10/$0.50 per million input/output tokens. No model quality claim is made; the live tool behavior remains to be smoke-tested. [model catalog](https://docs.digitalocean.com/products/inference/details/models/), [pricing](https://docs.digitalocean.com/products/inference/details/pricing/), [tool calling feature](https://docs.digitalocean.com/products/inference/details/features/).

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `uv run pytest tests/test_provider.py` | pass | 13 passed |
| `python3 -m py_compile app/provider.py scripts/check_provider.py` | pass | No syntax errors |
| `git diff --check` | not run | Workspace path reports “Not a git repository”; known workspace setup limitation |
| `python3 scripts/check_provider.py` | not run | Billable live call requires explicit invocation with a configured key; no live call made |

## Limits and decisions needed

The returned provider/tool behavior and model quality have not been tested live. The official docs explicitly name Haiku 5.5 tool calling; current docs for Qwen and DeepSeek omit it. Root owns the model default and environment documentation. No key or `.env` contents were inspected.

## Handoff

Files are ready for Sol review: `app/provider.py`, `tests/test_provider.py`, `scripts/check_provider.py`, and this report. Run the opt-in check only when the user intends to spend inference credits: `python3 scripts/check_provider.py`.

**Sol review:** accepted after code/source review. Sol fixed direct script imports, added bounded smoke tests and selected Haiku 5.5 in .env/.env.example. `python3 -m pytest tests/test_provider.py tests/test_provider_smoke.py tests/test_api.py tests/test_agent.py tests/test_integration.py -q`: 32 passed. Explicit live-check invocation exits safely before network because the key is still absent. No paid request made. The unchanged data/memory suites were not redundantly rerun.
