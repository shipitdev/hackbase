# Orchestrator state

Updated: 17 October 2026. **Stage: backend implemented and reviewed; frontend and live-provider acceptance pending.**

## User direction

User constraint: workers report on completion/blockers; Sol must not repeatedly poll them. Token conservation is required: compact packets/reports, relevant context only, logs saved by path and no redundant tool calls. No numerical token budget has been specified.

The current GPT-6.1 Sol session is the sole orchestrator. Delegate bounded implementation tasks to GPT-6 Luna, giving it relevant files/plan and AGENTS.md. Workers report back for Sol to review. Planning references are saved. User has now instructed us to build the backend and delegate work.

## Read on resume

1. `AGENTS.md`
2. `tasks/plan.md` and `tasks/todo.md`
3. `docs/orchestration.md`, `docs/system-design.md`, `docs/contracts.md`
4. `docs/diagrams/README.md` and relevant worker reports

## Decisions

- Luna high for non-trivial data/domain/memory/tool-loop work; medium for bounded UI/docs tasks. Recommendation pending real build calibration.
- Usually two workers concurrently; Sol owns contracts/integration/review and may use a third worker for an independent check.
- React/Vite + FastAPI + SQLite; shared knowledge separate from private conversation/results.
- Five runtime tools, corrected calculations, component-list GenUI, source inspection.
- User explicitly corrected the active calculation date to 2026-10-17. Original 16 October source-answer benchmarks are historical fixtures, not current-window guarantees; conversation/plan dates remain separate.
- Existing original research and dataset remain unchanged.
- Backend contract v1 is implemented; concrete classes/methods are in tasks/briefs/backend-interfaces.md.
- Runtime adapter: configurable Chat Completions. User switched preference to DigitalOcean serverless inference. Ignored .env created for GRADIENT_MODEL_ACCESS_KEY; configured model is now inference-router with budget preference. Live router tool check pending. Other compatible endpoints remain supported.

## Active assignments

Contract: tasks/briefs/backend-interfaces.md v1 frozen.

| Owner | Writable files | State |
|---|---|---|
| B1 Luna high | app/load.py, store.py, rules.py, reports.py; tests/test_store.py; report B1 | Implemented, reviewed and released |
| B2 Luna high | app/memory.py; tests/test_memory.py; report B2 | Implemented, reviewed and released |
| Sol | app/main.py, contracts.py, provider.py, agent.py, errors.py; API/provider tests; setup/docs | Implemented and reviewed |

Workers reported completion without status polling. B1 received bounded repair assignments after Sol found correctness/security issues. B2 also performed an independent read-only integration review. Both assignments are released. No live runtime provider key is configured; automated model calls are scripted.

## Verified so far

Initial dataset/doc audit and later GenUI resource review are recorded in `docs/00-review.md` and `docs/04-genui-and-context.md`. Planning checks passed: all local links/heading anchors across 19 Markdown files, three native Excalidraw scene structures, three SVG exports and text bounds. All three diagrams were rendered via MCP; PNG previews were visually inspected and labels adjusted. Luna-high review findings were addressed. These checks do not test an application/provider or constitute a native-file import round trip.

Backend implementation and checks: [integration report](reports/backend-integration.md). Real sample is loaded in ignored data/knowledge.sqlite. Tests include actual dataset analytics and the full HTTP/tool/result/source/private-recall path with a scripted model. Factual citations, private-message ownership, SQL CTE shadowing and dated override scope have regression checks.

## Open items

- Configure an API key or a local tool-capable model, then verify real model/tool behavior and all evaluation questions. Free provider availability/rate limits remain external constraints.
- Actual test dataset overlap/conflicting-ID policy if needed.
- User authorized GitHub sync to shipitdev/hackbase. Baseline published via GitHub connector: c7c93e21bf5da10598fa5c69dc9d0725a17728c4. Local .git creation remains blocked. Dataset/research checkouts, runtime DBs and keys are excluded.
- DigitalOcean integration accepted: B3 Luna high updated the existing HTTPX provider and a two-call smoke script. Sol fixed direct-script imports and tested the script with mocks. 32 relevant provider/smoke/API/agent/real-data integration checks pass. No repeated worker polling.
- Default .env/.env.example now select inference-router on inference.do-ai.run/v1 (changed after the account rejected Haiku). Official catalog confirms tools; pricing sources are in docs/digitalocean.md. User has $25 credits. This is not an app-enforced account spending cap; no auto fallback or HTTP retries.
- User added the model access key and set ANALYSIS_DATE=2026-10-17. Key presence verified without printing it. Live smoke attempted once, failed before HTTP because DNS cannot resolve inference.do-ai.run (gaierror errno8). Authentication and inference remain unverified; no billable completion received.
- Runtime health confirms data ready=true, chat_ready=true (configuration only), analysis_date=2026-10-17. Sol updated code defaults; Luna medium updated date guidance/windows. Historical sample tests explicitly retain16; real-data HTTP integration checks17. Date/API/smoke/store checks:14 passed.
- This workspace rejects local socket binding. Uvicorn reached app startup; HTTP behavior is verified using TestClient. Run the README server command from a normal local shell.
- Frontend/browser rendering, test-set release, complete model question evaluation and submission remain unimplemented/unverified.

## Next action

Next action: run python3 scripts/check_provider.py in a normal local shell with network access (workspace DNS is blocked), then one actual SQL/copilot question. Key is already configured. After live provider acceptance, build the frontend against docs/contracts.md. Keep six visual types, source inspection, user/thread switching and clear provider/partial-result errors. Follow exact file ownership and completion notifications. Do not rerun completed backend checks without a related change or unresolved risk.

## Current blocker: user's live HTTP 403

User's normal terminal now reaches HTTP403, while the agent workspace still cannot resolve/reach the endpoint. A fresh Luna-high worker verified endpoint/model/key/VPC/balance docs and added safe403 hints plus a GET-only --diagnose command. Sol reviewed and fixed balance phrase detection and diagnostic exit status. No model/key/scope was changed and no paid inference was made during this investigation. User was asked for the safe local diagnostic JSON and key-scope/VPC settings; actual403 cause remains unverified pending that information. Do not label inference fixed based on mock tests.

User's normal-terminal catalog result is now HTTP200/model_visible=true. This is catalog membership, not inference entitlement. Official DO limits exclude Anthropic from Tier1/2; root and worker verified this. Added fixed tier-denial hint; root rechecked25 provider/smoke tests (pass). Recommended next experiment: shell-only LLM_MODEL=openai-gpt-oss-120b override for the two-call smoke, a documented Tier1/2 exception. No `.env` model change or account upgrade performed. Still awaiting actual POST outcome/account tier.

## Latest account change

User reports previous account had zero inference credits and replaced the local model access key with a different account having $4 inference credit. Treat $4 as the current available balance, not the earlier $25 budget. Root attempted the existing two-call smoke once; it failed before HTTP due workspace DNS (gaierror errno8). New key authentication, account tier and live inference remain unverified. Do not print/commit .env or silently switch models. Next: user runs ordinary smoke in normal terminal; if denial persists, evaluate that new account's model eligibility and inference balance.

## Latest: managed router enabled

User confirmed an explicit account-tier403 and asked DigitalOcean to choose a model. Root changed only .env model/routing settings, preserving the private key: LLM_MODEL=inference-router, LLM_ROUTING_PREFERENCE=budget. B5 Luna high verified managed router docs and implemented provider payload plus served-model reporting; Sol added per-call served_models to saved copilot answers and router-scope guidance. No custom router/account resource was created. Current available inference credit is $4; budget preference is not a hard price limit. Router key scope and live tier behavior remain unverified. Next: user runs ordinary two-call smoke from normal terminal and shares safe summary.
