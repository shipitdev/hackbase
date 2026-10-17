# How Sol and Luna will build together

## Roles

Keep the current GPT-6.1 Sol session as the only orchestrator. It decides what to build next, defines the shared interfaces, gives workers focused context, reviews their output, joins the pieces and records progress.

Workers use GPT-6 Luna. **High is the default for non-trivial implementation; medium is for clear UI pieces, small changes and reports.** Escalate a repeatedly failing task to Sol with the failing example. More reasoning is not a substitute for missing context or a smaller assignment.

Official OpenAI documentation describes Luna as suited to scoped work and supports medium/high reasoning. The division above is our starting policy for this project, not a benchmark result. [Model selection](https://developers.openai.com/api/docs/guides/model-selection) · [Luna model](https://developers.openai.com/api/docs/models/gpt-6-luna).

## Three different meanings of “agent”

| Role | Where it exists | Responsibility |
|---|---|---|
| Build orchestrator | This Sol session | Plan, dispatch, review and integrate |
| Build workers | Delegated Luna sessions | Implement assigned files and return evidence |
| Copilot model | Inside the finished application | Answer operator questions by calling the app’s tools |

The build team is not a runtime multi-agent architecture. The application keeps the small tool loop in [the design](system-design.md). Its provider/model remains a separate preflight decision. Codex access does not by itself establish API credentials or the app’s provider compatibility.

## How many workers?

Normally run **two workers at once**, leaving Sol free to review/integrate. This session permits three non-root workers, but a third is useful only for a genuinely independent, usually read-only check. Do not fill slots just because they exist.

Start workers with fresh context and explicit model/effort settings. Give them a task packet; do not copy the whole long transcript. Workers can read additional relevant files, but cannot silently expand their scope or delegate again.

## Assignment lanes

| Lane | Default effort | Owns while assigned | Must not edit |
|---|---|---|---|
| Data and rules | Luna high | Loader/store/report reader and its focused tests | API contracts, frontend, private-memory implementation |
| Interface | Luna medium initially | Chat shell, allowed components, styles and UI fixtures | Backend contracts, domain rules, global dependency files |
| Copilot and memory | Luna high, after data interfaces settle | Tool loop/provider adapter or memory functions, as specifically assigned | Data-owned files and API composition |
| Verification | Luna high | Assigned scenario tests or read-only findings | Production fixes unless reassigned |
| Orchestrator | Sol | Shared contracts, API assembly, dependency changes, browser checks and integration | Active worker-owned files until ownership is returned |

These are reusable roles, not four permanent agents. The first data worker can later take a bounded memory task; the first UI worker can later prepare documentation.

## Notifications and token discipline

Workers notify Sol when complete or when a blocker needs a decision. Sol does not repeatedly list agents, check status, inspect unfinished reports or send progress requests. While they run, do independent work; otherwise wait for a completion notification using the available waiting mechanism, without a short-interval polling loop. Investigate a reported blocker, tool failure or missed agreed deadline when needed.

Keep dispatch briefs normally within 250 words, with file paths and relevant sections instead of copied documents. Completion messages normally fit within 200 words: changed files, check outcomes, remaining issue and report path. Detailed logs stay in files. No routine progress chatter or duplicate delivery of a full report into chat.

Read each completed report and the relevant changes once, then run the necessary acceptance/integration check. Broaden investigation only for a concrete failure or risk. Do not cut required checks to meet a token target; narrow the assignment instead. Any explicit remaining token budget should constrain packet size and concurrency. No numeric budget has been supplied yet.

## Dispatch → build → report → accept

1. Sol chooses the next unchecked task and a useful slice of it, lists exact allowed files and assigns a time budget.
2. Sol writes a brief using [the template](../tasks/brief-template.md), records ownership in [state](../tasks/state.md), and sends the worker the brief path plus required context.
3. Worker confirms scope, reads the relevant files, implements and runs the specified checks. It reports an interface gap before changing a shared contract.
4. Worker writes `tasks/reports/<task>-<lane>.md` using [the report template](../tasks/report-template.md), then sends Sol the path and a short summary.
5. Sol reads the changed code and report, reruns the important check, and checks the actual user-facing behavior when relevant. Fake UI fixture success does not count as a working backend flow.
6. Sol accepts or returns one concrete repair task. Only Sol updates `tasks/todo.md` and `tasks/state.md`.

A report can say partial or blocked. No agent may convert a failing required check into a passing one by deleting assertions, skipping a required feature or hardcoding the sample result.

## Shared-workspace rules

Use disjoint files, not competing edits. The orchestrator approves a small dependency change and performs package/lockfile updates once. Avoid parallel database writes during load/schema changes. Worker tests use isolated temporary databases, not the active demo store.

Do not assume worktrees are necessary: the app repo does not exist yet. If isolation becomes useful after repository setup, Sol may assign separate branches/worktrees with an explicit integration step. Nothing here authorizes publication or merges.

## What a worker needs in its packet

A goal, relevant task IDs, allowed files, frozen interface names, source/rule references, expected behavior, focused check command, time budget and where to save its report. Include what must remain unchanged and known source ambiguities.

For example, a map task needs the component contract, result columns, styling/layout notes and Q7—not every regulatory rule or the whole private-memory discussion.

## Keep the orchestrator recoverable

After each accepted slice, save the current result, active owners, unresolved issues, commands and next action in `tasks/state.md`. Keep tool output/test details in worker reports, not the main context window. On resume or compaction, read that file before redispatching or repeating work.

Do not claim the current context window lasts indefinitely. The files make a resumed orchestrator able to continue the same plan.

## Ownership transfer record

Every active assignment in `tasks/state.md` lists its exact writable files, report path, contract revision and whether ownership is active or returned. Reused files such as `app/store.py`, `app/agent.py` and `frontend/src/App.tsx` transfer between slices only after the previous worker reports it has stopped editing and Sol records the handoff. Checklist “likely files” do not grant concurrent ownership.
