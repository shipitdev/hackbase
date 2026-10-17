# Video pitch script — under five minutes

Read the quoted paragraphs. The bracketed lines are recording directions. **Latest rehearsal evidence:** after the validation fix, the exact Q9-2 prompt returned Nathan Pierce and 150 wells with 3 citations in 37.8 seconds. It retained explicit limitations; the full suite has not been rerun. Rehearse before recording. The final evaluation is complete; the figures below describe observed responses, not an accuracy pass rate.

## 0:00–1:20 — Design

[Show `docs/diagrams/system-design.svg`. Follow the arrows as you speak.]

“Oil-field information is spread across readings, repair reports, rules and operator notes. I built a chat interface that brings those sources together and lets someone inspect where an answer came from.

“The dataset goes through a loader into the shared database. It contains 600 wells across seven areas. For this final dataset, today means 15 January 2027.

“When I ask a question, the backend checks the selected user and conversation. The copilot uses a language model hosted by DigitalOcean and gives it five tools: database queries for numbers, evidence for original records, search for documents, recall for earlier chats, and remember for explicit shared facts or corrections.

“The two databases serve different purposes. Shared facts are available across users. Private chats and saved results belong to the selected user. Corrections keep the original reading available. This prototype uses a demo user picker; production sign-in would be separate.

“The model also proposes a display using OpenUI. The dashed arrow shows that proposal. The backend checks the display against saved results, then the browser renders it. The chart or table uses saved rows rather than numbers invented inside a display.”

## 1:20–3:35 — Exact final-test showcase

[Select Robert Hayes and start a fresh chat. Use Q9 turn2 exactly as written in the official final test set. It was the clearest factual answer in the completed run. The original test asks it within a multi-topic session; using it alone here is a standalone demonstration, not a replay of the entire Q9 scenario.]

**Main prompt — final Q9, turn 2, exact wording:**

> Different topic. Who leads Northwest Production, and how many wells does that team run?

**Observed final-test answer:** Nathan Pierce leads Northwest Production; the team runs 150 wells. The returned answer had four citations and an explicit data-currentness limitation. Its key facts were independently checked against the source database. No table was requested or generated for this turn.

“I’m using a question from the final evaluation. It asks who leads Northwest Production and how many wells the team runs. Our evaluated answer identified Nathan Pierce and 150 wells. I’ll run it here and open the evidence.”

[Submit once. Show the actual answer and a citation. Identical wording and successful delivery are not guaranteed. Do not add an untested table instruction.]

**Backup — final Q1, exact wording; Michael Turner, fresh chat:**

> All our wells feed one reservoir. Map the reservoir pressure across the field from the pressure data.

**Observed E4 behavior:** It refused to invent a map because calibrated pressure measurements are absent, with cited source checks. Engineering pressure limits and separator alarms are not reservoir-pressure measurements.

“This backup final-test question shows a data boundary. The system explains that reservoir pressure was not measured instead of inventing a map.”

[Show the actual response and its source evidence. If it fails, show that failure and proceed to the results.]

## 3:35–4:20 — Latest results and limits

“We reran all 11 final questions and follow-ups:21 turns in order. Twelve returned partial responses and nine returned provider errors. No call timed out in this run, but most partials did not contain usable answers.

“Two turns returned source-supported answers: the reservoir-pressure refusal and the team-lead question. The other 19could not be verified. That is two supported answers out of 21 attempts, not a general accuracy percentage.

“The remaining blockers were context growth and provider compatibility at the final-answer stage. The write-up includes the failures, and the saved answer bundle preserves every turn. The next step is to verify the provider compatibility repair, reduce repeated context, and rerun the affected cases.”

## Before recording

- Use a readable full-screen diagram; Shared DB is the upper cylinder, Private DB the lower cylinder. The dashed arrow carries the proposed UI; saved results provide the values.
- Rehearse the live question. Allow time for inference; the timestamp ranges are a guide, not a latency guarantee.
- Keep the first evaluation unchanged. Label later reruns separately.
- A diagram and narrated expectation are not proof of a successful live answer. Show the actual outcome and preserve its qualifications.

Final evaluation: `tasks/reports/E3-final-evaluation.md`. No dollar-cost claim is made because timeout usage is incomplete. No broad accuracy percentage is justified.
