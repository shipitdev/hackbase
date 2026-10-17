import { useMemo, useState } from "react";
import { Renderer } from "@openuidev/react-lang";
import { ResultsProvider, resultLibrary, validateProgram } from "../genui/library";
import type { Answer, Evidence, SavedResult } from "../types";

function resultColumns(result: SavedResult) {
  return result.columns.map((column) => column.name);
}

function HistoricalViews({ answer }: { answer: Answer }) {
  const results = { ...(answer.results ?? {}) };
  for (const citation of answer.citations ?? []) {
    const value = citation.content as SavedResult | undefined;
    const id = citation.id ?? citation.reference;
    if (id && value && Array.isArray(value.columns) && Array.isArray(value.rows)) results[id] = value;
  }
  if (!answer.components?.length) return null;
  return <section className="historical-block" aria-label="Historical visual results">
    <p className="history-label">Historical result · original view format</p>
    {answer.components.map((component) => {
      const result = results[component.result_id];
      const requested = component.mapping.columns ?? component.mapping.fields ?? [];
      const columns = (Array.isArray(requested) ? requested : [requested]).filter((name): name is string => typeof name === "string");
      const visible = columns.length ? columns : result?.columns.map((column) => column.name) ?? [];
      return <div className="historical-result" key={component.id}>
        <h3>{component.title}</h3>
        {result ? <ResultTable columns={visible} result={result} /> : <p>Saved result details are not available in this message.</p>}
        {component.type !== "table" && component.type !== "card" && <p className="muted">This {component.type} was saved in the earlier answer format; its source data is shown above.</p>}
      </div>;
    })}
  </section>;
}

function ResultTable({ columns, result }: { columns: string[]; result: SavedResult }) {
  if (!result.rows.length) return <p className="muted">No rows were returned.</p>;
  return <div className="table-scroll"><table><thead><tr>{columns.map((name) => <th key={name}>{result.columns.find((column) => column.name === name)?.label ?? name}</th>)}</tr></thead>
    <tbody>{result.rows.map((row, index) => <tr key={index}>{columns.map((name) => <td key={name}>{String(row[name] ?? "Unknown")}</td>)}</tr>)}</tbody></table></div>;
}

export function AnswerView({ answer, onSource }: { answer: Answer; onSource: (source: Evidence) => void }) {
  const [renderError, setRenderError] = useState("");
  const results = useMemo(() => Object.fromEntries(Object.entries(answer.results ?? {}).map(([id, result]) => [id, { columns: resultColumns(result), rows: result.rows }])), [answer.results]);
  let validUi = false;
  let validationError = "";
  if (answer.ui_format === "openui-lang" && answer.ui) {
    try { validateProgram(answer.ui, results); validUi = true; }
    catch (error) { validationError = error instanceof Error ? error.message : "The saved visual could not be validated."; }
  }
  const citations = answer.citations ?? [];
  return <div className="answer-content">
    <p className="answer-copy">{answer.answer}</p>
    {answer.analysis_date && <p className="answer-date">Calculated for {answer.analysis_date}{answer.status === "partial" ? " · Partial answer" : ""}</p>}
    {answer.conflicts?.length ? <section className="notice notice-amber"><h3>Disagreement to review</h3>{answer.conflicts.map((conflict, index) => <p key={index}>{conflict.claim ?? "Conflicting evidence was recorded."} {conflict.status ? `(${conflict.status})` : ""}</p>)}</section> : null}
    {answer.limitations?.length ? <section className="notice"><h3>Limits of this answer</h3><ul>{answer.limitations.map((item, index) => <li key={index}>{item}</li>)}</ul></section> : null}
    {validUi && <section className="openui-result"><ResultsProvider value={results}><Renderer response={answer.ui!} library={resultLibrary} onError={(errors) => setRenderError(errors.length ? "The saved visual could not be rendered." : "")} /></ResultsProvider></section>}
    {(validationError || renderError) && <p className="inline-error" role="status">Visual unavailable: {validationError || renderError}</p>}
    {!answer.ui && <HistoricalViews answer={answer} />}
    {citations.length > 0 && <section className="source-list" aria-label="Sources"><h3>Sources</h3><div>{citations.map((source, index) => {
      const reference = source.id ?? source.reference;
      return <button key={`${reference ?? "source"}-${index}`} className="source-button" type="button" disabled={!reference} onClick={() => onSource(source)}>
        <span>{source.title ?? reference ?? "Source"}</span><small>{reference ?? source.kind ?? "Evidence"}</small>
      </button>;
    })}</div></section>}
  </div>;
}
