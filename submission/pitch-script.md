# Video pitch script — under five minutes

Read the quoted paragraphs. The bracketed lines are recording directions. The final evaluation is complete; the figures below describe observed responses, not an accuracy pass rate.

## 0:00–1:20 — Design

[Show `docs/diagrams/video-system.svg`. Follow the arrows as you speak.]

“Oil-field information is spread across readings, repair reports, rules and operator notes. I built a chat interface that brings those sources together and lets someone inspect where an answer came from.

“The dataset goes through a loader into the shared database. It contains 600 wells across seven areas. For this final dataset, today means 15 January 2027.

“When I ask a question, the backend checks the selected user and conversation. The copilot uses a language model hosted by DigitalOcean and gives it five tools: database queries for numbers, evidence for original records, search for documents, recall for earlier chats, and remember for explicit shared facts or corrections.

“The two databases serve different purposes. Shared facts are available across users. Private chats and saved results belong to the selected user. Corrections keep the original reading available. This prototype uses a demo user picker; production sign-in would be separate.

“The model also proposes a display using OpenUI. The dashed arrow shows that proposal. The backend checks the display against saved results, then the browser renders it. The chart or table uses saved rows rather than numbers invented inside a display.”

## 1:20–3:35 — Live demo

[Use Robert Hayes and a fresh chat. Rehearse once before recording. This question's key facts were verified in final evaluation Q9-2 and independently checked against the source database. The shorter standalone wording below has not had a separate live run.]

“Let me show a simple question with an answer we can check.”

[Ask: **Who leads Northwest Production, and how many wells does that team run?**]

“The source records identify Nathan Pierce as the lead, and the team has 150 wells. I’ll open the evidence behind the answer.”

[Wait for the actual answer; show its citations. If it fails or differs, say so. Do not read the expected answer as though the UI returned it.]

[Optional, only if rehearsal succeeds: ask **Show that team’s wells in a table with well ID and area.** This visual follow-up has not been validated by the final evaluation. Otherwise use the already captured Q2 table below.]

[If the table follow-up succeeds, point out one row and open its source.]

“The model chose the table layout, but the rows come from the saved database result. The server checks that the display refers to that result.”

[If the follow-up fails, show the failure honestly and move to the results. Do not claim the visual worked.]

## 3:35–4:20 — Results and limits

“We ran all 11 final questions, including their follow-ups: 21 turns in order. Sixteen returned partial responses and five timed out. A partial response did not necessarily contain a useful answer, so I’m not calling those sixteen successes.

“Two turns had supported key conclusions: the system correctly said oil volume was not measured, and it correctly identified Northwest Production’s lead and its 150 wells. Most complex questions did not produce enough evidence to assess. The main failures were context and answer-validation limits, plus provider timeouts.

“The next step is to improve how the system retrieves smaller pieces of evidence and finishes a valid answer, then rerun the affected cases. The data and display boundaries are implemented, but this final evaluation shows that the reasoning flow still needs work.”

## Before recording

- Use a readable full-screen diagram; Shared DB is the upper cylinder, Private DB the lower cylinder. The dashed arrow carries the proposed UI; saved results provide the values.
- Rehearse the live question. Allow time for inference; the timestamp ranges are a guide, not a latency guarantee.
- Keep the first evaluation unchanged. Label later reruns separately.
- A diagram and narrated expectation are not proof of a successful live answer. Show the actual outcome and preserve its qualifications.

Final evaluation: `tasks/reports/E3-final-evaluation.md`. No dollar-cost claim is made because timeout usage is incomplete. No broad accuracy percentage is justified.
