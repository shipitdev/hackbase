# What we need to build

Build a chat assistant for the supplied fictional oil field. People ask ordinary questions; it finds the relevant records, does the calculations, explains the answer and shows a useful visual.

Official sources: [problem](../dataset/01-problem-statement.md), [data guide](../dataset/02-dataset-guide.md), [example questions](../dataset/03-evaluation-queries.md), [setup guide](../dataset/04-prerequisites.md).

## What a successful app does

| Requirement | What the user should experience |
|---|---|
| Correct answers with evidence | Numbers come from records and the supplied rules. Clicking a source shows what supports the answer. Missing evidence is stated. |
| Generated interface | The model chooses and combines cards, tables, line charts, bar charts, maps and heatmaps for the question. If the user requests a visual, include it. |
| Shared well knowledge | Jake tells the app about planned work. Michael can later ask about it and see Jake’s note. |
| Private conversation memory | Michael can refer to wells discussed in an earlier chat. Jessica cannot inherit that discussion. A user picker is enough for the demo. |
| Learning from corrections | Keep the original value, the new value, who changed it and why. Use the correction for all users, only where it applies. |
| Honest disagreements | Show conflicting records and statements. A casual “running fine” claim must not silently replace a sensor reading. |
| New-data support | Load the released test dataset without changing code to recognize particular wells or questions. |

A shared fact is different from a private discussion: “WELL-0007 has a planned workover” is shared; “these are the three wells Michael compared” is private.

## Rules that drive the answers

- **Producing oil:** wellhead temperature minus air temperature is at least 15°C for T200 or 20°C for T350. “Now” means the latest inspection, using accepted corrections.
- **Downtime:** each inspection showing no production counts as seven days. A missed inspection adds nothing. Do not add repair-job hours instead.
- **Spills:** a confirmed false-positive correction removes that detection from counts, volumes and spill reporting duties. A person’s uncertain opinion does not automatically do this.
- **Corrections have consequences:** changing 4.5 to 5.4 barrels makes a spill reportable. Recheck notice and cleanup duties, even if the old report said otherwise.
- **Compliance needs distinct labels:** proven failure, possible failure with no supporting record, future/pending action, met/closed, or unknown.

The full rules are in [02-dataset.md](02-dataset.md). These are fictional challenge rules, not real operating guidance.

## Dates

Use **16 October 2026** as the date for calculations. Do not use the laptop’s current date. Source timestamps are UTC.

| Question wording | Dates to use in the sample |
|---|---|
| Last four months | 16 June–16 October 2026 |
| Last twelve months | 16 October 2025–16 October 2026 |
| Last four years | 16 October 2022–16 October 2026 |
| Last 90 days | 18 July–16 October 2026 |
| Last thirteen weeks | Start 91 days before today; sample readings run 23 July–15 October |
| This year | 1 January–16 October 2026 |

Include the stated start and end dates. In code, use the start date and stop before midnight after the end date. Subtract calendar months/years, not approximate day counts. Count a repair and its cost by its **start date**, including ongoing jobs.

Conversation time is separate. Q11 tests “yesterday” across two conversation days while calculations stay pinned to 16 October. A note’s planned dates are also separate: a shutdown starting tomorrow does not make a well down today.

## The four-hour deadline

Have the sample system working within two hours. The final two hours bring new data and final questions: load the data, record answers, fix important problems and submit.

Submit through OrganizerHQ:

- A **2–3 page** write-up. Aim for two readable pages: design on page one, final answers/results and failures on page two. Use a third if needed.
- A video of **at most five minutes**, in your own voice, explaining the build and showing a real question running through the UI.
- A public GitHub repository with an open-source license and run instructions. Exclude keys and private runtime chats.

The results page must contain the actual final answers. Reliability matters more than claiming every question worked.

## Leave out of this build

Model training, image analysis, replacement evidence photos, vector-search infrastructure, agent frameworks, enterprise login, deployment infrastructure and automatic field/regulator actions. Keep all six requested visual types and the required memory behavior.
