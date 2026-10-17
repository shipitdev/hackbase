# Video pitch script (target: 4:20–4:50)

**Recording note:** Final evaluation is still underway. Replace bracketed fields only after checking each answer against its cited source and saved result. Keep the first evaluation output unchanged; label any separate rerun. Do not invent answers, pass rates, or cost figures.

## 0:00–1:30 — How it works (about 90 seconds)

**[Show `docs/diagrams/video-system.svg` full screen.]**

“This system turns the supplied well records and operating documents into answers people can inspect. A checked loader puts the records into a shared database and keeps the originals. Accepted corrections affect later calculations at their stated scope; the original reading remains available.

“When someone asks a question in the browser, the backend checks the selected user and conversation. The copilot works with the configured DigitalOcean language model and can call five tools. SQL runs approved database queries. Evidence opens a cited source. Search finds useful documents. Recall reads that user’s earlier chats. Remember records a clear correction or shared fact after the server checks it.

“Shared well facts and private chats live separately. Private reads use the user selected by the backend, and saved results belong to that user and conversation. So a chart can use the same checked numbers as the answer without exposing another person’s chat.

“The backend checks the model’s OpenUI description against those saved results. The browser then renders the allowed cards, tables, and charts from the saved rows. The model suggests the presentation; the application makes sure it uses saved numbers and results belonging to the selected user.”

## 1:30–4:15 — Live use case (about 2:45)

**[Switch to the running browser. Show the selected demo user and a fresh dedicated chat.]**

“I’ll ask one question that has been checked against its source.”

**[After evaluation and source review, replace this with the exact question: `[VERIFIED QUESTION]`. Submit it once and show the completed response.]**

“Here is the answer. This table or chart uses the saved result the backend checked. I can open the citation to see the source behind the statement.”

**[Show the cited source, then return to the answer. Mention actual figures and units only after verifying them.]**

“The visual uses the same saved rows, so its numbers stay tied to the answer. If evidence is incomplete or disagrees, the answer should show that limit.”

**[Ask a short, source-supported follow-up: `[VERIFIED FOLLOW-UP]`. Show its response and source or saved result.]**

“Follow-ups can use this conversation and, when relevant, this user’s earlier private chat. Private reads are checked against the selected user. This is a local demo with a user picker; production sign-in would be a separate step.”

**[If the selected verified case includes a correction, show its scope and the original source reading. Otherwise skip this optional shot.]**

“An accepted correction affects later calculations only at its stated scope, and the original source value remains available. A casual claim stays attributed; it does not silently rewrite a measured reading.”

**[Show a meaningful limitation or disagreement from the verified case, if available.]**

## 4:15–4:45 — Close (about 30 seconds)

“We reviewed `[X/Y reviewed]` final scenarios; `[verified outcome]`. The main limitation was `[main limitation]`. This demo shows one use case checked against its source, with the answer, evidence, and saved visual connected.”

Keep the finished video under five minutes. The timing above leaves room for the real response and source panel.
