# DigitalOcean runtime model

The copilot uses DigitalOcean's serverless Chat Completions endpoint through the existing HTTPX adapter. No droplet, GPU rental, agent deployment or provider SDK is needed. This changes the app's runtime model, not the Sol/Luna development workflow.

## Setup

1. Open the ignored root `.env` (copy `.env.example` if absent).
2. Paste your DigitalOcean **model access key** after `GRADIENT_MODEL_ACCESS_KEY=`. Do not use a key in a command argument or chat message.
3. Leave `LLM_BASE_URL=https://inference.do-ai.run/v1`. Set `LLM_MODEL` to the verified catalog ID recorded below.
4. Restart the API using the README command. Project `.env` settings load automatically; existing shell variables take precedence.

The backend accepts `LLM_API_KEY` as a generic override. A DigitalOcean-specific key must never be sent to an unrelated provider host. Neither test reports nor errors should expose credentials or raw provider responses.

## Small verification before the full evaluation

Run `python3 scripts/check_provider.py` from the project after adding the key. It makes at most two short inference calls to test a function-tool request and tool-result continuation. This is a paid, opt-in check; automated unit tests use HTTP mocks and spend no credits. It does not prove SQL accuracy.

Then exercise one real production-status question through `/api/chat`, checking its SQL/result, cited inspection/manual, and returned component data. Only after that passes should we run the broader question set. Record failures rather than silently changing providers or benchmarking every model.

## Budget: $25 available

Use the existing single provider, eight-round maximum, 120-second answer limit, 96,000-character context limit and 4,096-token output limit per regular model call. The small smoke uses a much smaller output allowance. No background model jobs, automatic paid fallback, or automatic HTTP retries are configured.

These request limits are **not a $25 account-wide spending cap**. DigitalOcean charges reported inference usage against eligible promotional credits/prepaid balances; verify that your credits appear in the inference balance and keep auto-reload disabled if you want spending limited to available credit. Other projects using the same account can also spend it. Check provider usage/balance before running a large evaluation.

## Model choice and sources

Selected model: `anthropic-claude-5.5-haiku` (Claude Haiku 5.5). DigitalOcean explicitly lists tool calling. Published rates for prompts up to 100K tokens are $0.10 per million input tokens and $0.50 per million output tokens; prompts over 100K are priced differently. This is an economical candidate, not a claim of proven SQL accuracy.

For scale, 10,000 input tokens plus 2,000 output tokens cost about $0.002 at those rates, before any cache adjustments. An app answer may make several model calls. The tiny two-call smoke has at most 512 generated tokens total; it is for connectivity/function use, not a performance benchmark.

Qwen and DeepSeek remain potential alternatives, but the catalog did not explicitly confirm function calling for the checked entries. Do not infer that they lack the capability; test before switching.

Official references:

- [Endpoints](https://docs.digitalocean.com/products/inference/how-to/si-endpoints/): `/v1/models`, `/v1/chat/completions`, model access authentication.
- [Chat Completions guide](https://docs.digitalocean.com/products/inference/how-to/use-chat-completions-api/): message and tool protocol.
- [Available models](https://docs.digitalocean.com/products/inference/details/models/): exact model IDs/capabilities.
- [Pricing](https://docs.digitalocean.com/products/inference/details/pricing/): per-model token pricing and prepaid-credit rules. Checked 17 October 2026; confirm current prices before changing models.

Local Git metadata cannot currently be created in this workspace. GitHub sync uses the GitHub connector and explicitly selected source/docs files; `.env`, databases, dataset and research checkouts are excluded.

## Current validation

The user configured the key and changed the calculation date to **17 October 2026**. Backend health confirms the date and credential configuration. A live smoke attempt failed before HTTP because this workspace cannot resolve the inference hostname; this does not validate or invalidate the key. Run `python3 scripts/check_provider.py` from a normal local terminal. No successful billable inference has been observed.

## Diagnose HTTP 403

Run `python3 scripts/check_provider.py --diagnose` from the terminal that received the 403. This requests only the model catalog, makes no inference calls, and prints a fixed diagnostic summary without response bodies or keys. A nonzero exit means the check did not confirm catalog visibility. Catalog visibility alone does not prove inference authorization.

If denied, inspect the existing key in **Model Access Keys**: confirm that its model list includes the configured model and that its VPC setting permits this laptop. A Wi-Fi private-network setting is unrelated to a DigitalOcean VPC. Key model/VPC scopes cannot be changed after creation; if they are wrong, create an appropriately scoped key and replace only the local .env value. Do not rotate keys speculatively. Check eligible inference/promotional/prepaid balance if access or balance is suspended. See [DigitalOcean key settings](https://docs.digitalocean.com/products/inference/how-to/manage-model-access-keys/).

After catalog access is confirmed, rerun the ordinary small smoke to test inference. If only inference returns403, its fixed guidance can help distinguish model scope or billing from catalog access. If the category is unknown, account/provider investigation is still required; the app does not bypass403 or silently fall back to another paid model.

## Catalog succeeds but Haiku inference returns403

The user confirmed `http_status:200, model_visible:true` for `/models`. This confirms catalog visibility only. DigitalOcean's [Inference limits](https://docs.digitalocean.com/products/inference/details/limits/) explicitly exclude Anthropic models for Tier1 and Tier2 accounts, even though the catalog can list them. Account tier is therefore a plausible cause; the actual account tier and POST denial reason remain unverified.

Test a documented Tier1/2 exception without changing `.env`:

```sh
LLM_MODEL=openai-gpt-oss-120b python3 scripts/check_provider.py
```

The command makes at most two small inference requests; it is not an automatic fallback. DigitalOcean's ID is `openai-gpt-oss-120b`; published input/output pricing is $0.10/$0.70 per million tokens. The original model supports function calling ([OpenAI model docs](https://developers.openai.com/api/docs/models/gpt-oss-120b)); DigitalOcean's hosted behavior still needs this test. Keep the existing `.env` model until a tool roundtrip is confirmed. A token-limit/truncation error would be a separate issue from403 and should be diagnosed separately. Do not pay for an account upgrade just to test this hypothesis.
