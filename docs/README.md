# Asset Intelligence Copilot — build notes

These notes explain what to build, why, and how to fit it into four hours. The backend is implemented; live domain acceptance and native OpenUI frontend work are in progress.

**For orchestration, start with [AGENTS.md](../AGENTS.md), [current state](../tasks/state.md) and [the four-hour plan](../tasks/plan.md).** For a human overview, read [the proposed design](strategy.md). Use the other files when you need a rule, an expected answer or the reason behind a decision.

| File | What it explains |
|---|---|
| [00-review.md](00-review.md) | What changed from the earlier research |
| [01-problem.md](01-problem.md) | What the challenge requires |
| [02-dataset.md](02-dataset.md) | What is in the data and how the rules work |
| [03-questions.md](03-questions.md) | What each of the 18 example questions must demonstrate |
| [04-genui-and-context.md](04-genui-and-context.md) | What the supplied GenUI and memory resources mean for our build |
| [05-frontend-openui.md](05-frontend-openui.md) | Native OpenUI generation, six displays, validation and build slices |
| [strategy.md](strategy.md) | The design decisions, in plain English |
| [system-design.md](system-design.md) | Application modules and the question-to-answer flow |
| [contracts.md](contracts.md) | Shared API, results and UI component shapes |
| [orchestration.md](orchestration.md) | Sol/Luna roles, ownership and review rules |
| [ui-layout.md](ui-layout.md) | Chat layout and interaction states |
| [diagrams/README.md](diagrams/README.md) | Editable Excalidraw system, build workflow and UI drawings |
| [tasks/plan.md](../tasks/plan.md) | Where the four hours go |
| [tasks/todo.md](../tasks/todo.md) | What to build and how to check each step |

A few terms used in these notes:

- **GenUI:** the model chooses and combines interface elements for the current question.
- **Tool:** a function the model can ask the application to run, such as a database query.
- **Context:** the information sent to the model for its current response.
- **Memory:** information saved so it can be used in a later response or chat.
- **Correction scope:** exactly which inspection, well or well type a correction affects.
- **RCA:** root-cause analysis: investigating why equipment keeps failing.

The original research in `opencode/docs/` is unchanged. These notes replace its build recommendations. The official challenge files remain the source of requirements.

Dataset reviewed: `dataset/`, commit `b8de8c9bd68f40334e5d06922126169e4f3bf3ca`, matching GitHub main during the initial review. [Official repository](https://github.com/FlytBaseAILabs/flytbase-ahc-swe-asset-intelligence-dataset/tree/b8de8c9bd68f40334e5d06922126169e4f3bf3ca).
