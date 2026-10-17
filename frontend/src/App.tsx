import { FormEvent, KeyboardEvent as ReactKeyboardEvent, useEffect, useRef, useState } from "react";
import { api } from "./api";
import { AnswerView } from "./components/AnswerView";
import type { Answer, Evidence, Health, Message, Thread, User } from "./types";

const id: () => string = () => globalThis.crypto?.randomUUID?.() ?? `${Date.now()}-${Math.random().toString(36).slice(2)}`;
const safeText = (value: unknown) => typeof value === "string" ? value : JSON.stringify(value, null, 2) ?? "No evidence content.";

export default function App() {
  const [users, setUsers] = useState<User[]>([]);
  const [userId, setUserId] = useState("");
  const [health, setHealth] = useState<Health | null>(null);
  const [threads, setThreads] = useState<Thread[]>([]);
  const [threadId, setThreadId] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [pageError, setPageError] = useState("");
  const [busy, setBusy] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [evidenceError, setEvidenceError] = useState("");
  const [evidenceBusy, setEvidenceBusy] = useState(false);
  const [retry, setRetry] = useState<{ request_id: string; text: string } | null>(null);
  const [creatingThread, setCreatingThread] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const turn = useRef(0);
  const evidenceTurn = useRef(0);
  const activeSend = useRef<{ epoch: number; request_id: string } | null>(null);
  const creatingRef = useRef(false);
  const navTrigger = useRef<HTMLButtonElement>(null);
  const userPicker = useRef<HTMLSelectElement>(null);
  const evidenceClose = useRef<HTMLButtonElement>(null);
  const evidenceTrigger = useRef<HTMLElement | null>(null);
  const hadMobileNav = useRef(false);
  const conversationRef = useRef<HTMLElement>(null);

  useEffect(() => {
    let live = true;
    Promise.all([api.health(), api.users()]).then(([status, list]) => {
      if (!live) return;
      setHealth(status); setUsers(list);
      if (list[0]) setUserId(list[0].user_id);
    }).catch((error) => live && setPageError(error.message));
    return () => { live = false; };
  }, []);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 700px)");
    const update = () => setIsMobile(media.matches);
    update(); media.addEventListener("change", update);
    return () => media.removeEventListener("change", update);
  }, []);

  useEffect(() => {
    if (mobileNav) {
      hadMobileNav.current = true;
      userPicker.current?.focus();
    } else if (hadMobileNav.current) {
      hadMobileNav.current = false;
      navTrigger.current?.focus();
    }
  }, [mobileNav]);

  useEffect(() => { if (evidence) evidenceClose.current?.focus(); }, [Boolean(evidence)]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key !== "Escape") return;
      if (mobileNav) setMobileNav(false);
      else if (evidence) closeEvidence();
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [mobileNav, evidence]);

  useEffect(() => {
    if (!userId) return;
    const epoch = ++turn.current;
    setMessages([]); setThreads([]); setThreadId(""); setEvidence(null); setEvidenceError(""); setPageError(""); setRetry(null); setBusy(false);
    api.threads(userId).then(async (list) => {
      if (turn.current !== epoch) return;
      setThreads(list);
      if (list[0]) setThreadId(list[0].thread_id);
      else {
        const created = await api.newThread(userId);
        if (turn.current !== epoch) return;
        setThreads([created]); setThreadId(created.thread_id);
      }
    }).catch((error) => turn.current === epoch && setPageError(error.message));
  }, [userId]);

  useEffect(() => {
    if (!userId || !threadId) return;
    const epoch = turn.current;
    setMessages([]); setPageError(""); setRetry(null);
    api.messages(userId, threadId).then((list) => turn.current === epoch && setMessages(list)).catch((error) => turn.current === epoch && setPageError(error.message));
  }, [userId, threadId]);

  useEffect(() => {
    const conversation = conversationRef.current;
    if (conversation) conversation.scrollTo({ top: conversation.scrollHeight });
  }, [messages, busy]);

  async function chooseUser(next: string) {
    if (next === userId) return;
    ++turn.current;
    clearEvidence(); setMessages([]); setThreads([]); setThreadId(""); setRetry(null); setBusy(false); setDraft("");
    setMobileNav(false);
    setUserId(next);
  }

  async function createThread() {
    if (!userId || creatingRef.current) return;
    creatingRef.current = true;
    setCreatingThread(true);
    const epoch = ++turn.current;
    clearEvidence(); setMessages([]); setThreadId(""); setDraft(""); setBusy(false); setRetry(null);
    setPageError("");
    try {
      const thread = await api.newThread(userId);
      if (turn.current !== epoch) return;
      setThreads((items) => [thread, ...items]); setThreadId(thread.thread_id); setMessages([]); setMobileNav(false);
    } catch (error) { if (turn.current === epoch) setPageError((error as Error).message); }
    finally { creatingRef.current = false; setCreatingThread(false); }
  }

  async function selectThread(thread: Thread) {
    if (thread.thread_id === threadId) return;
    ++turn.current;
    clearEvidence(); setMessages([]); setBusy(false); setRetry(null); setDraft("");
    setThreadId(thread.thread_id); setMobileNav(false);
  }

  async function send(text: string, request_id = id()) {
    if (!userId || !threadId || creatingThread || !text.trim()) return;
    const epoch = turn.current;
    if (activeSend.current?.epoch === epoch) return;
    const operation = { epoch, request_id };
    activeSend.current = operation;
    const payload = { request_id, user_id: userId, thread_id: threadId, text: text.trim() };
    setBusy(true); setPageError(""); setRetry(null); setDraft("");
    setMessages((items) => [...items, { message_id: `pending-${request_id}`, role: "user", text: payload.text, created_at: new Date().toISOString() }]);
    try {
      const answer: Answer = await api.chat(payload);
      if (turn.current !== epoch) return;
      setMessages((items) => [...items.filter((message) => message.message_id !== `pending-${request_id}`),
        { message_id: `user-${request_id}`, role: "user", text: payload.text, created_at: new Date().toISOString() },
        { message_id: answer.message_id ?? `assistant-${request_id}`, role: "assistant", text: answer.answer, answer, created_at: new Date().toISOString() }]);
      setThreads((items) => items.map((thread) => thread.thread_id === threadId && thread.title === "New conversation" ? { ...thread, title: payload.text.slice(0, 80) } : thread));
    } catch (error) {
      if (turn.current !== epoch) return;
      setMessages((items) => items.filter((message) => message.message_id !== `pending-${request_id}`));
      setDraft(payload.text); setRetry({ request_id, text: payload.text }); setPageError((error as Error).message);
    } finally {
      if (activeSend.current === operation) activeSend.current = null;
      if (turn.current === epoch) setBusy(false);
    }
  }

  function sendDraft() {
    const sameFailedRequest = retry && draft.trim() === retry.text ? retry : null;
    void send(draft, sameFailedRequest?.request_id ?? id());
  }
  function submit(event: FormEvent) { event.preventDefault(); sendDraft(); }
  function keySubmit(event: ReactKeyboardEvent<HTMLTextAreaElement>) { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendDraft(); } }

  function clearEvidence() {
    ++evidenceTurn.current;
    setEvidence(null); setEvidenceError(""); setEvidenceBusy(false);
  }

  function closeEvidence() {
    clearEvidence();
    evidenceTrigger.current?.focus();
  }

  async function openEvidence(source: Evidence) {
    const reference = source.id ?? source.reference;
    if (!reference || !userId) return;
    evidenceTrigger.current = document.activeElement as HTMLElement | null;
    const epoch = ++evidenceTurn.current;
    setEvidenceBusy(true); setEvidenceError(""); setEvidence(source);
    try {
      const loaded = await api.evidence(userId, reference);
      if (evidenceTurn.current === epoch) setEvidence(loaded ?? source);
    } catch (error) { if (evidenceTurn.current === epoch) setEvidenceError((error as Error).message); }
    finally { if (evidenceTurn.current === epoch) setEvidenceBusy(false); }
  }

  const selected = users.find((user) => user.user_id === userId);
  return <div className="app-shell">
    {mobileNav && <button className="scrim" aria-label="Close navigation" onClick={() => setMobileNav(false)} />}
    <aside className={`sidebar ${mobileNav ? "sidebar-open" : ""}`} aria-label="Chat navigation" inert={isMobile && !mobileNav} aria-hidden={isMobile && !mobileNav}>
      <div className="brand"><span className="brand-mark">AI</span><div><strong>Asset Intelligence</strong><small>Field operations copilot</small></div></div>
      <label className="field-label" htmlFor="user-select">Demo user</label>
      <select ref={userPicker} id="user-select" value={userId} onChange={(event) => void chooseUser(event.target.value)} disabled={!users.length}>
        {users.map((user) => <option key={user.user_id} value={user.user_id}>{user.name} · {user.role}</option>)}
      </select>
      <button className="new-chat" onClick={() => void createThread()} disabled={!userId || creatingThread}>＋ <span>{creatingThread ? "Creating conversation…" : "New conversation"}</span></button>
      <div className="thread-heading"><span>Conversations</span><span>{threads.length}</span></div>
      <nav className="thread-list" aria-label="Saved conversations">
        {threads.map((thread) => <button key={thread.thread_id} className={`thread-item ${thread.thread_id === threadId ? "selected" : ""}`} onClick={() => void selectThread(thread)} title={thread.title}>
          <span className="thread-dot" />{thread.title || "New conversation"}
        </button>)}
        {!threads.length && <p className="sidebar-muted">Loading conversations…</p>}
      </nav>
      <div className="sidebar-foot"><span className={`status-dot ${health?.ready ? "online" : ""}`} />{health?.ready ? "Dataset connected" : "Connecting to API"}</div>
    </aside>

    <main className="chat-column">
      <header className="topbar">
        <button ref={navTrigger} className="mobile-menu" aria-label="Open navigation" onClick={() => setMobileNav(true)}>☰</button>
        <div><span className="eyebrow">ASSET INTELLIGENCE</span><h1>{selected ? `${selected.name}’s workspace` : "Workspace"}</h1></div>
        <div className="date-chip"><span>Calculation date</span><strong>{health?.analysis_date ?? "2026-10-17"}</strong></div>
      </header>

      <section ref={conversationRef} className="conversation" aria-label="Conversation" aria-live="polite">
        {!messages.length && !busy && <div className="welcome">
          <span className="welcome-kicker">FIELD OPERATIONS · {health?.ready ? "READY" : "CONNECTING"}</span>
          <h2>What would you like<br />to inspect?</h2>
          <p>Ask about well status, production, maintenance, or the evidence behind a result.</p>
          <div className="suggestions"><button onClick={() => setDraft("Show the latest inspection findings")}>Latest inspection findings <span>→</span></button><button onClick={() => setDraft("Which wells need attention?")}>Wells that need attention <span>→</span></button></div>
        </div>}
        <div className="message-list">
          {messages.map((message) => <article key={message.message_id} className={`message message-${message.role}`}>
            {message.role === "assistant" ? <><div className="assistant-label"><span className="assistant-mark">AI</span><span>Asset Intelligence</span></div><AnswerView answer={message.answer ?? { answer: message.text }} onSource={(source) => void openEvidence(source)} /></> : <p className="user-copy">{message.text}</p>}
          </article>)}
          {busy && <div className="pending"><span className="pending-mark">AI</span><div><strong>Reviewing the records</strong><span className="skeleton" /><span className="skeleton short" /></div></div>}
        </div>
      </section>
      <div className="composer-wrap">
        {pageError && <div className="error-bar" role="alert"><span>{pageError}</span>{retry && <button onClick={sendDraft} disabled={busy || creatingThread}>Retry</button>}</div>}
        <form className="composer" onSubmit={submit}>
          <label className="sr-only" htmlFor="prompt">Ask a question about your assets</label>
          <textarea id="prompt" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keySubmit} placeholder="Ask about your assets…" rows={1} disabled={busy || creatingThread || !threadId || !health?.chat_ready} />
          <button type="submit" aria-label="Send question" disabled={busy || creatingThread || !draft.trim() || !threadId || !health?.chat_ready}>{busy ? "…" : "↑"}</button>
          <small>Enter to send · Shift + Enter for a new line</small>
        </form>
      </div>
    </main>

    <aside className={`evidence-panel ${evidence ? "evidence-open" : ""}`} aria-label="Evidence details" inert={!evidence} aria-hidden={!evidence}>
      <div className="evidence-head"><div><span className="eyebrow">REFERENCE</span><h2>Evidence</h2></div><button ref={evidenceClose} aria-label="Close evidence" onClick={closeEvidence}>×</button></div>
      {!evidence && <div className="evidence-empty"><div className="evidence-rule" /><h3>Sources stay inspectable</h3><p>Select a source from an answer to read its record, report excerpt, or rule reference.</p></div>}
      {evidence && <div className="evidence-body"><span className="evidence-kind">{evidence.kind ?? "Source"}</span><h3>{evidence.title ?? evidence.id ?? evidence.reference}</h3>
        {(evidence.id || evidence.reference) && <code>{evidence.id ?? evidence.reference}</code>}
        {evidenceBusy && <p className="muted">Loading source…</p>}{evidenceError && <p className="inline-error" role="alert">{evidenceError}</p>}
        {evidence.content !== undefined && <pre>{safeText(evidence.content)}</pre>}
        {evidence.source_path && <p className="muted">{evidence.source_path}</p>}
        {evidence.metadata && <pre>{safeText(evidence.metadata)}</pre>}
      </div>}
    </aside>
  </div>;
}
