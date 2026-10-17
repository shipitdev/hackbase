# UI layout reference

See the editable [Excalidraw layout](diagrams/copilot-layout.excalidraw) and its preview in the [diagram index](diagrams/README.md). This is a wireframe, not a claim that the UI already exists.

## Desktop layout

Use a quiet light background, dark readable text and one blue accent. Amber means disagreement/pending attention; red is an actual error/breach, and green indicates a supported positive status. Color is always accompanied by text.

**Left, about 220px:** app name, user picker, New chat button and that user’s thread list. Switching user closes private chat/results from the previous user and loads only the new user’s history.

**Center, flexible:** header with current user and visible calculation date, conversation messages and generated answer blocks. A message can contain prose, a card/chart/table/map/heatmap, and a clear disagreement strip. The model chooses blocks/order for the question; the app supplies actual result data. Keep the input fixed at the bottom of the conversation area.

**Right, about 300px when open:** evidence panel. A source click shows the record/report excerpt, source ID, rule section, author/time if relevant and applied correction. Collapse it by default on small screens. No permanent dashboard beside the chat.

The specific WELL-0001 example in the drawing is demonstration content only. UI code must render any well/result from the server, not embed this answer.

## Shared presentation rules

- Always show observation dates and units; distinguish the calculation date from the current conversation timestamp.
- Status cards show the temperature difference, applicable threshold and original/corrected value where relevant.
- Charts have readable axes/legends. Stopped readings need a marker as well as color.
- Tables and map details remain keyboard-accessible; charts expose a detail table. Heatmaps label zero counts.
- Shared claims/corrections show who supplied them. Private thread names never become shared well facts.
- Source details are inspectable, not just decorative citation badges.

## Required states

| State | What to show |
|---|---|
| First use | Brief prompt, user selection and example question suggestions; no precomputed fake answers |
| Waiting | Visible pending state, input disabled or guarded against duplicate send, safe error recovery |
| Complete | Generated components with matching numbers, sources and dates |
| Disagreement | Both sides with attribution; the supported calculation and any request to clarify |
| Correction saved | What changed, original/new values, scope, author and downstream consequences |
| No results | Clear empty table/map; no fabricated rows |
| Partial evidence | Visible limitation and what could not be read/checked |
| Failed visual/provider | Readable error; preserve message text and allow retry without duplicate writes |

On mobile, turn the left navigation into a drawer, stack answer components and open sources as a full-width panel. No keyboard trap; provide focus labels, visible focus and adequate contrast.

## GenUI acceptance check

Ask for a ranking and supporting details: the model should be able to choose a bar chart plus table. Ask for a status with a disagreement: show a card plus warning and source links. Change a reading, then check all components in the next answer use the correction. Check the actual browser rather than only the returned JSON.
