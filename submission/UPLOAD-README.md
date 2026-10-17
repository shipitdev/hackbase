# FlytBase submission files

Use writeup.pdf as the two-page write-up. writeup.docx is an editable companion; PDF pagination is the verified version.

Upload the PDF to Google Drive, enable viewer access for the intended judges, and paste its share link into the Write-up link field. The recorded video and public repository link are separate submission items. This ZIP is a collection of artifacts; check the portal's accepted file types before uploading the ZIP itself.

Public repository: https://github.com/shipitdev/hackbase

The evaluation report summarizes the completed E4 full run. The two-page write-up also records the in-progress context-pipeline evaluation snapshot; see context-pipeline-status.md for its exact scope and limits. final-answers.html and answers/ preserve each official turn's captured answer, visual specification, saved table rows, citations and errors. They contain neither runtime SQLite databases nor private tool traces. HTTP success is not an accuracy pass. Diagrams and the pitch script are reference material for the video.

The narrated video is NOT included: record and upload it separately, at most five minutes. Final submission through the event portal remains your action.

Version note: E4 was captured before the final R4 tool-choice compatibility repair. That later repair passed61 focused offline tests but has not had a paid live retest. Its existence does not change the reported E4 outcomes.

Post-E4 context note: bounded previews and compaction passed 75 focused offline checks. One later Q4 attempt returned without a context-limit failure or timeout but failed final JSON validation and produced no table. See the separate post-fix report; this does not change the E4 counts in the two-page write-up. The earlier Q4 attempt was not retried; a separate final-suite evaluation is now in progress.

Repository requirement: the event asks for an open-source license. This repository currently has no LICENSE file; choose and add a license before final submission.


The context-pipeline run was still active at the time of packaging: 16/21 turns attempted, 11 HTTP 200 partials, 4 HTTP 502 errors, and 1 pending request. No correctness claims are made for those new responses. Do not compare these incomplete counts as an accuracy score.
