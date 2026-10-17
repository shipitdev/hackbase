# GenUI and context: what we should use

**Recommendation:** let the model combine a small set of UI components around verified query results. Keep the full records and history saved, while sending only relevant information to the model. We do not need to reproduce a research training setup to meet this challenge.

The source summaries below describe what was checked. The build choices are our recommendations for the four-hour constraint; they are not requirements imposed by these resources.

## What the supplied resources tell us

| Resource | What was checked and the useful idea |
|---|---|
| [OUI-1 announcement](https://www.openui.com/blog/oui-1) | OUI-1 is a specialized model that writes OpenUI Lang. The article emphasizes checking whether generated interfaces are structurally valid. A UI benchmark result does not establish correctness on our well questions. |
| [When Interfaces Speak](https://arxiv.org/pdf/2610.11123) | Read the paper’s task definition and design. It retrieves database evidence, generates an interface to collect needed user input, then uses tools to complete the task. Our takeaway: useful UI should help people inspect or resolve a question, not just look impressive. |
| [Ruben Casas talk](https://www.youtube.com/watch?v=hCMrEfPG2Yg&t=1s) | Read the [publisher’s talk notes](https://ai.engineer/talks/hCMrEfPG2Yg-generative-ui-for-mcp). It distinguishes fixed components, model-composed descriptions, and generated frontend code. Composition gives flexibility while keeping approved building blocks; generated executable code needs containment. |
| [Google Cloud GenUI session](https://youtu.be/UsMDkEsR-ok?si=3oeeUq9jh8R08fSU) | Checked the official title/description and [A2UI comparison docs](https://a2ui.org/introduction/agent-ui-ecosystem/), not the full video transcript. A2UI describes the UI; AG-UI connects the agent and frontend; MCP Apps provide another way to deliver interfaces. These are different jobs, not three libraries we must install together. |
| [GateMem](https://arxiv.org/pdf/2606.18829) | This is specifically a shared-memory governance benchmark, covering permitted recall, access boundaries, updates and forgetting. It supports testing who may receive remembered information, not just whether the system remembers it. It does not require us to add a new memory framework or a deletion feature to this challenge. |
| [Sally-Ann DeLucia talk](https://www.youtube.com/watch?v=esY99nYXxR4) | Read the [publisher’s talk notes](https://ai.engineer/talks/esY99nYXxR4-we-solved-context-management-in-agents). Its useful lesson is to keep large material recoverable outside the active prompt and test later conversation turns. The talk’s truncation sizes are workload examples, not settings to copy blindly. |

Direct YouTube playback/transcripts were not available through the browsing tool. The two AI Engineer talk summaries use the publisher’s written material; the Google session review is limited to its official description and linked documentation. No claim here relies on watching all three videos.

## What counts as GenUI for this app?

The official challenge asks for an answer generated for the current question, with the appropriate inline visual. It does not require a particular framework or newly generated React code. [Challenge requirement](../dataset/01-problem-statement.md).

We can define reusable components while allowing the model to decide which to use, how to combine them, and what data they show. OpenUI’s own [documentation](https://www.openui.com/docs) describes that approach and supports using your own components and model. OpenUI is the rendering toolkit; OUI-1 is a particular model. Choosing the toolkit does not require choosing that model.

Our earlier single-visual design can cover the examples, but allowing a few components per answer makes it more useful:

| User asks | Generated answer can contain |
|---|---|
| “Is this well producing?” | Status card, disagreement warning if needed, expandable evidence |
| “Which wells were down longest?” | Bar chart, supporting table, date/rule explanation |
| “Show the real spills on a map” | Map, clickable spill details, corrected-detection explanation |
| “That reading is wrong” | Before/after card, attribution and any remaining disagreement |

The component selection and order change with the question; this is not a set of fixed question-specific screens.

## The smallest implementation

Have the model produce an ordered list of allowed components. Each data component points to a saved tool result. The application supplies its actual numbers and checks the component name, columns and access permissions.

For example, the description can mean: “Show result R1 as a bar chart, then as a table, followed by its sources.” The model chooses the presentation; it does not rewrite the measurements.

Support the six required data displays plus ordinary text, a disagreement notice and expandable source details. Existing table sorting, map popups and source inspection provide useful interaction. Add a new clarification form only if a real question needs it; do not require an extra approval click for every clear correction.

**Updated user decision:** use OpenUI and let the model generate OpenUI Lang directly. The earlier JSON-first recommendation is superseded for the new frontend. Keep result-backed data, private memory and source checks; first prove the official parser and renderer work with our component library. See the [native OpenUI plan](05-frontend-openui.md).

Do not introduce a second UI model, arbitrary generated code, a training pipeline or multiple UI protocols just to match a resource’s architecture. Keep database calculations, memory and evidence independent of the UI library.

## Context engineering, in everyday terms

**Memory is what we save. Context is what we put in front of the model right now.**

For each question, provide:

1. The selected user, the calculation date and the tool instructions.
2. The small rulebook.
3. Recent relevant conversation and exact previously discussed well IDs, only for that user.
4. Relevant shared notes, corrections and unresolved disagreements.
5. The query results and report excerpts needed for this answer.

Do not send 40,000 inspections, all reports, every user’s history or the whole debugging log. Let SQL calculate large totals. Keep full results saved and reopen them by reference when needed. Make any shortened output explicit; never shorten away a correction or disagreement that changes the answer.

## Checks added to the build

- Ask a new question that needs a chart **and** supporting detail; inspect that the model chooses the combination.
- Change a reading and check every displayed component uses the corrected result.
- Add ten unrelated turns, then ask about an earlier well set; verify the references survive.
- Switch users and repeat the recall request; private history must not cross over.
- Click sources and test an empty or invalid visual description in the browser.

These checks make the ideas useful to this build without adding a research project inside the hackathon.
