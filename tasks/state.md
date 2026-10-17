# Orchestrator state

Updated 17 October 2026. **E4 evaluation and local submission bundle complete; R5 runtime context repair active.**

## Stable decisions

- Sol sole orchestrator; Luna high for backend/data/debugging, medium for bounded UI. Exact file ownership, fresh scoped context, no child agents/status polling. Workers notify completion. Active final evaluation ownership is listed below.
- Analysis date **2027-01-15**; conversation time separate. Historical16October fixtures retained.
- Runtime DigitalOcean `inference-router`, budget preference, user budget$25 (no hard cap). Key only ignored.env, never print/publish. No runtime model change or paid test in final sprint.
- Direct model-generated OpenUI Lang; same-library schema/prompt. No model-authored rows or arbitrary browser code/actions. Root/server owns calculations/results/private identity. Demo user picker is not public authentication.
- GitHub shipitdev/hackbase; dataset/,opencode/ preserved/ignored. Runtime databases/chats/screenshots/keys and installed .agents/skills ignored. Taste skill installed; original v1 app guidance used because default v2 excludes apps.

## Implemented

FastAPI/SQLite corrected restricted queries, reports/rules/evidence, scoped shared corrections preserving originals, private chats/results, idempotent retries. Final release600wells/125198inspections/17415maintenance/4437readable reports loaded; original sample backed up. Loader rejects collisions and preserves history/feedback.

Native six-view contract in docs/contracts.md: Card/Table/Bar/Line/Map/Heatmap, max6 static views. Official Node parser, same-user/thread/revision and full-row numeric/coordinate/boolean/cell checks; only server-saved values hydrate. Current prompt teaches SQLite and explicit heatmap zero-grid queries. One shared bounded repair for oversized tool batches/final validation,8rounds/120s/96k context retained. Original provider HTTP errors expose only safe accumulated model/usage/latency metadata.

React chat: real users/threads/history, source panel, conflict/limitation states, safe explicit retry, stale reply guards and private-state clearing. Six displays stack at readable answer width. Full viewport grid/flex min-size fixes and scoped scrolling prevent generated outputs moving/expanding outer page. Wide tables/line plots scroll internally. Leaflet map observes resize and has tile-failure/coordinate-table fallback. OpenUI inspector disabled via documented pinned-version bootstrap shortcut.

## Evidence and limits

- E1 all18 sample scenarios attempted:29turns,19HTTP200 partials,8errors,2blocked. **Not18/18passed.** Reviewed table tasks/reports/E1-reviewed-results.md. Several shared writes persisted despite response timeouts; never assume rollback. Q18 yes+both notes aligns with official source; resolved wording needs semantics review, no blanket conflict rewrite.
- R1 worker51 focused runtime/API/provider checks; E2 worker11 offline runner checks. Runner fences paid dispatch/replay, checks persisted prerequisites/exact Q6 list, owner-qualifies threads, orders per-message timestamps/restores clock and captures safe error metadata. Original E1 immutable. Fresh output selection/Q16 prior-history setup remain limitations before another full run.
- Final sprint root44 focused backend/parser/API/preflight tests passed; final OpenUI six-view SSR/parser/bridge/example checks and strict TS/Vite build pass. npm audit0.
- Actual browser six-view fixture with35rows/20columns/longtext at320/390/768/1024/1440 and resize-back: viewport stable, composer visible, internal scrolling,0visual errors. Map3points/popup/realtiles and blocked-tile fallback checked. Screenshots inspected and ignored. These prove rendering, **not live model selection or final question correctness**.
- Prior actual Q1 native Card+Table passed data/source checks with limitations after manual retry,64s. Provider timeouts/latency still unresolved. No broad paid rerun.

## Release readiness and immediate next actions

1. Final baseline activated from official commit009e2b5; see docs/released-data.md. Version dataset-7207fefc8284, revision1, analysis2027-01-15. Both databases backed up; private memory counts verified unchanged.
2. Delegate targeted live checks/new final questions with isolated/resumable evidence capture. Preserve scenario dependencies and private history. Do not let old E1 --resume silently represent a new run.
3. Complete submission/writeup.md from actual results, select/add license, export2–3pages, record<=5minute demo, verify links. No event submission without authorization.

## Run / references

Backend localhost8000: `python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000`.
Frontend localhost5173: `npm --prefix frontend run dev`. Node22.12+ and frontend dependencies also needed by backend validator. Both local servers are running; backend was restarted with final Python integration.

Current plan tasks/plan.md final-priorities section; checklist tasks/todo.md. Reports F6-final-sprint.md, F4-layout.md, F5-six-visuals.md, D1-release-readiness.md, R1-runtime-reliability.md, E2-evaluation-review.md. Generated schema/prompt `npm --prefix frontend run check:openui -- --write`; normal check catches drift. Submission draft is not final/complete.

## Accepted F7 Send-control fix
Luna medium implemented shrinkable grid row/sidebar and bounded scrollable error text; Send/Sending label retained with existing accessible name. Root removed hard320px body min-width that clipped zoomed narrow views.20browserchecks across empty/typed/busy/long-error/generated-table at CSS widths256/312/614/1152 pass; final frontend production build passes. No paid model calls; no backend restart needed. All F7 files returned. Report tasks/reports/F7-send-button.md.

## Final release activation in progress
- Official dataset commit `009e2b5`; final release 600 wells/7 areas, today 2027-01-15, 11 ordered multi-turn questions.
- Backup: ignored `data/backups/before-final-20261017-164055/`; both SQLite stores preserved; zero shared changes at backup. Backend restarted PID32961, exec session36170, health ready/chat_ready.
- D2 compatibility accepted; ownership returned. T500 thresholds, source data corrections, history/status/raw payload columns integrated. Worker8 focused tests pass; root release test1pass, agent20pass, API4pass; frontend build pass.
- Ownership active: final_eval Luna high owns scripts/evaluate_final.py, tasks/reports/E3-final-evaluation.md and private data/evaluations/final-release/. Root authorized paid run after activation. Snapshot isolated, ordered, no automatic retries; root does not run paid evaluation.

## Video assignment
- Accepted video_demo Luna medium; ownership returned: docs/diagrams/video-system.excalidraw, docs/diagrams/video-system.svg, submission/pitch-script.md, tasks/reports/V1-video-demo.md. One-/two-word diagram labels, database shapes, actual runtime flow, simple narrated script; accuracy placeholders pending E3. No application changes or paid calls.

V1 accepted: 16:9 editable Excalidraw + SVG, mixed shapes/database cylinders, five tools and saved-result/nativeUI flow reviewed. Pitch script ~90sec design + live demo + results placeholders, total<5min. MCP checkpoint397bfffa662d43ee82. User records narration/demo; final accuracy still awaits E3.

## E3 final evaluation reviewed
- All21turns/11scenarios attempted:16HTTP200 partial,5HTTP504; no complete statuses. Most partials contain no usable evidence, not16passes.
- Supported key conclusions: Q2 no measured oil volume; Q9-2 NathanPierce and150Northwest wells (root independently checked). Other fullscenario accuracy unproven; Q8-4 persisted a sharedclaim only in isolated evalDB and must not be treated as verified pump replacement.
- Final_eval ownership returned; rawresults ignored data/evaluations/final-release/, report tasks/reports/E3-final-evaluation.md. No retries or tuning occurred. ActiveDB stillrevision1/zerochanges.
- Pitch updated with observedresults and realistic nextsteps. Fixed missing native Excalidraw standalone text dimensions, including SharedDB label; MCP checkpoint9c29955606604823a6. Demo rehearsal/livefollowup remain unverified.

## R2 timeout repair active
User authorized fixing/increasing timeouts. Luna high owns app/provider.py, app/agent.py, tests/test_provider.py, tests/test_agent.py, tasks/reports/R2-timeout-fix.md. No paidcalls yet; configurable provider/total budgets, focused tests, no silent retries/modelchanges. Root owns settings/restart/script. Demo script now uses exact finalQ9-2 and finalQ2, without invented prompts or requested visuals absent from those original turns.

R2 code accepted/ownershipreturned: validated provider/answer time budgets; root56tests pass. Active.env90spercall/240stotal; Viteproxy300s (previously150). BackendPID35450 exec58888; proxyhealthready. final_eval owns scripts/check_timeout_fix.py, tasks/reports/R2-live-check.md and ignored timeout-fix outputs; authorized exactlyQ9-2 andQ4 once each afteractivation, noauto retries. No contextcap/modelchange.

## R3 validation repair active
R2 targetedQ9-2/Q4 checks bothavoidedtimeouts butreturnedemptyvalidationpartials (~29/~82sec). Demo is not reliableyet. Luna timeout_fix owns app/agent.py/tests/test_agent.py/tasks/reports/R3-validation-fix.md: distinguishsafevalidationreasons, reserve2of8roundsforfinalsynthesis/repair, preservegrounding. No historicaldrafterrorssaved, so specificsunknown. final_eval willfinishR2report thenprepareONEfreshQ9-2 postR3check in separatevalidation-fix folder; paidcallawaitsactivation.

## W1 submission writeup active
video_demo owns submission/asset-intelligence-writeup.docx/.pdf, scripts/build_writeup.py, tasks/reports/W1-writeup.md; intermediates ignoreddata/writeup. Exactly2pages: design+SVG then11question observedresults. NativeDriveimportunavailabledespiteinstalledplugin; userinformedrefresh/manualupload. Workspaceartifactruntime/markerunavailable; rootapprovedavailablelocalPDF/DOCXfallback, nohostLibreOffice/globalinstalls. DeliverPDFprimarywithpageQA.

R3codeaccepted/ownershipreturned: root60tests pass, backendPID36226 exec18716 restarted. SinglefreshQ9-2 paidcheckauthorizedinvalidation-fix outputfolder; no fullrerun. W1writeupcontinuesindependently.

R3targetedlivecheckdone: exactQ9-2returnedNathanPierce/150with3citations in37.759s, partialwithexplicitlimitations. InitialJSONdraftinvalid; finalrepairrecovered, safeprivate tracecaptured. No remainingvalidationerroronthatturn; notfullsuiterun. W1workerinformedtoincludeasclearlyseparatelatercheck. Drivebrowseruploadblockedbypermissiondecline; noalternate-routeupload.

## E4 fresh full rerun authorized
Userrequestsallfinalevalsagainandnewoutputs/accuracyinlocal2pagedoc. final_evalownsNEWtasks/reports/E4-final-rerun.md+ignoreddata/evaluations/final-rerun/. All11/21once, inordersharedisolatedmemory, currentR3+90/240settings; noautopaidretry. W1workerfinisheslayout/buildernow; finaldocmustbeupdatedafterE4beforepresentedasfinal. Userwilluploadlocallysavedfiles; noDriveaccessattempts.

## E4 completed and packaging
All21turnscomplete:12HTTP200partial,9HTTP502upstream400,0HTTP504. Tenpartialscontext-limited; onlyQ1refusal/Q9-2Nathan150useful+source-supported. No suiteaccuracy% claimed (2/21verifiedcoverageisnotgeneralaccuracy). E4reporttasks/reports/E4-final-rerun.md; fullanswersexportedignoreddata/submission/final-rerun/. W1workerupdatingfinal2pagePDF/DOCXnow. FinalZIPmustexcludekeys/DBs/private traces andwillincludePDF,DOCX,fullanswersHTML/JSON,report,diagram/script/README; videonotrecorded/notincluded.

## Local submission bundle ready
AcceptedW1E4refresh: submission/asset-intelligence-writeup.pdf exactly2pages, bothpagesrootvisuallychecked, DOCXcompanionfullfigure/sanitizerchecked. LocalignoredZIPsubmission/flytbase-submission.zip:30files/21answercaptures, PDF/DOCX+report+sourcechecks+diagram/script+README. Integrityandkeyexclusionspass; novideo/DBs/privatetraces. UserwilluploadmanualDrive. R4workerownsprovider/agent/testsforboundedtool-choicecompatibilityrepair; nofurtherpaidcalls. FullE4resultsremainimmutable.

R4compatibilityaccepted: providerkeepsdefinitions+tool_choice:none insynthesis; root61focusedtestspass, restartedafterconfirmingnopendingliverequests. No postR4paidcheck, E4scoresunchanged. Allworkerownershipreturned. FinalZIPincludesversionnoteandR4report; videoandportal/Driveuploadremainuseractions.

## R5 context repair active
context_fix Luna high owns app/agent.py, app/store.py, tests/test_agent.py, tests/test_store.py, tests/test_context_budget.py, tasks/reports/R5-context-fix.md. Userauthorizedcontextfix. Shrink/dedupeprompttoolpreviews, proactiveboundedcompactionpreservingreferences/protocol/evidence/privateaccess. Keepfullsavedrows andexisting96kcap/8rounds/R4tool-choice contract; nopaidcalls. RootreviewsbeforetargetedLunaQ4check, nofullsuiteautomaticrerun. ExistingPDF/ZIPreportE4andarenotnewfixscores.

R5reviewrequestedbeforeactivation: explicitget_evidence re-read/pagingmustaccesspost-previewtextandmustnottruncatefinalcitationhydration; wideSQLpreviewmustretainstructuredresultmetadata ratherthanencodedprefix. RootauthorizedoptionalEvidenceArgsoffset/limitforpromptpreviewonly. Workeraddingtestswithrealistic37kbase andaccuratepagingoffsets. NoR5paidcallorbackendactivationyet.

R5acceptedandactivated: onlyapp/agent.py +newtests, no store/memorydatachanges. OptionalEvidenceArgs pagingpreviewonly; dedupsearch/boundedSQLmetadata/proactive72kcompaction. Rootfixedfullnestedbody/limitations/claimmetadata preservation;75focusedtests pass. BackendPID39673exec63811 active; targetedLunaQ4once authorized andrunning. READMEc231ef8pushed; R5GitHubsyncnext. E4PDF/ZIPscoresstillunchanged.

## R5 targeted outcome
OneQ4callreturned200partialin180.653s,8modelcalls,134706recordedtokens. No contextcap/timeout, buttwofinaldraftsfailedJSONvalidation andnouitable/citations/resultsreturned. Notapass; no furtherpaidcalls queued. FullE4scoresunchanged. READMEandZIPaddendumwillrecordthisbeforefinalpush.
