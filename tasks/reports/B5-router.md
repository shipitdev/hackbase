# Worker report: B5 — DigitalOcean Inference Router

**Worker/model/effort:** GPT-6 Luna / high (explicit assignment)  
**Status:** accepted by Sol for integration; live acceptance pending  
**Interface revision:** B5 router smoke

## Delivered

The adapter now accepts `LLM_MODEL=inference-router` and adds `routing_preference` only for that model at DigitalOcean. `LLM_ROUTING_PREFERENCE` accepts `balanced`, `budget`, or `quality`; it defaults to `budget`. DigitalOcean's returned `model` is surfaced by the adapter and both served model IDs appear in the smoke summary. Other providers retain their existing payload. No dependencies or account changes.

Official docs identify `inference-router` as a built-in router enabled for all users; no custom router ID or console router creation is needed. Chat Completions body:

```json
{"model":"inference-router","routing_preference":"budget","messages":[...],"tools":[...],"max_completion_tokens":256,"stream":false}
```

Use the same `https://inference.do-ai.run/v1/chat/completions` endpoint and model access key. The key must include access under **Inference routers** (all routers or the selected router); existing key scope/VPC settings cannot be edited. Routing is free in public preview, but each request is billed at the model that serves it, reported in response `model`. Current reported balance is $4; no inference was called here. [Router guide](https://docs.digitalocean.com/products/inference/how-to/use-inference-router/) · [key scopes](https://docs.digitalocean.com/products/inference/how-to/manage-model-access-keys/) · [pricing](https://docs.digitalocean.com/products/inference/details/pricing/)

DigitalOcean's limits still say Tier 1 and 2 accounts cannot use Anthropic models. Router docs do not state that routing bypasses tier or key/model eligibility; therefore a router call may still fail if the request resolves to an ineligible model. A `budget` preference is not a guarantee of a particular model. [limits](https://docs.digitalocean.com/products/inference/details/limits/)

## Checks

| Command or manual check | Outcome | Evidence / exact failure |
|---|---|---|
| `uv run pytest tests/test_provider.py tests/test_provider_smoke.py` | pass | 30 passed; routing payload/default/validation, tool payload, served-model reporting, and no leakage to other providers. |
| `python3 -m py_compile app/provider.py scripts/check_provider.py` | pass | Both modules compile. |
| Official DigitalOcean router, limits, key-scope, and pricing docs | pass | Links above; router docs last verified 12 Oct 2026, limits 12 Oct 2026, key scopes 6 Oct 2026, pricing 15 Oct 2026. |
| Live two-call smoke | not run | Paid inference explicitly excluded from this assignment. |

## Limits and decisions needed

The user's account tier and key's router scope remain unknown. The docs do not promise the router can bypass Tier 1/2 model restrictions. Verify the router key scope and make the small smoke only from the user's network when they choose to spend credits.

## Handoff

Changed: `app/provider.py`, `scripts/check_provider.py`, `tests/test_provider.py`, `tests/test_provider_smoke.py`, and this report. Suggested user-network check: `LLM_MODEL=inference-router python3 scripts/check_provider.py`; it makes up to two paid requests and reports the actual served model for each.

**Sol review:** provider/smoke reviewed; Sol configured managed budget routing, added saved-answer serving-model provenance and safe router-scope guidance. Live tool behavior remains unverified; no account-tier bypass is claimed.
