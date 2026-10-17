import React, { createContext, useContext, useEffect, useRef, useState } from "react";
import { createLibrary, createParser, defineComponent, type Library } from "@openuidev/react-lang";
import { BarChartCondensed } from "@openuidev/react-ui";
import { z } from "zod/v4";

export type ResultData = { columns: string[]; rows: Record<string, unknown>[] };
export type Results = Record<string, ResultData>;

const ResultsContext = createContext<Results>({});
export const ResultsProvider = ResultsContext.Provider;

const resultId = z.string().min(1).max(80);
const title = z.string().min(1).max(160);
const column = z.string().min(1).max(80);
const fields = z.array(column).min(1).max(20);
const UiNode = z.union([
  z.lazy(() => ResultCard.ref), z.lazy(() => ResultTable.ref), z.lazy(() => ResultBar.ref),
  z.lazy(() => ResultLine.ref), z.lazy(() => ResultMap.ref), z.lazy(() => ResultHeatmap.ref),
]);

const AnswerLayout = defineComponent({
  name: "AnswerLayout",
  description: "Root layout that composes up to six result-backed views.",
  props: z.object({ children: z.array(UiNode).min(1).max(6) }),
  component: ({ props, renderNode }) => <div className="answer-layout">{renderNode(props.children)}</div>,
});

const ResultCard = defineComponent({
  name: "ResultCard",
  description: "Shows selected fields from one row in a server-saved result.",
  props: z.object({ resultId, title, fields }),
  component: ({ props }) => {
    const { row } = oneRow(props.resultId);
    return <View title={props.title}><dl className="genui-card-values">{props.fields.map((field) => <div key={field}><dt>{field}</dt><dd>{display(row?.[field])}</dd></div>)}</dl></View>;
  },
});

const ResultTable = defineComponent({
  name: "ResultTable",
  description: "Shows selected columns from a server-saved result.",
  props: z.object({ resultId, title, fields }),
  component: ({ props }) => {
    const data = useResult(props.resultId);
    return <View title={props.title}><DataTable columns={props.fields} data={data} /></View>;
  },
});

const ResultBar = defineComponent({
  name: "ResultBar",
  description: "Compares a numeric result column across categories.",
  props: z.object({ resultId, title, category: column, value: column }),
  component: ({ props }) => {
    const data = useResult(props.resultId);
    const rows = data?.rows ?? [];
    const chartRows = rows.flatMap((row) => {
      const value = numeric(row[props.value]);
      return value === null ? [] : [{ category: display(row[props.category]), value }];
    });
    return <View title={props.title}>
      {chartRows.length ? <div className="genui-chart"><BarChartCondensed data={chartRows} categoryKey="category" height={Math.min(420, Math.max(180, chartRows.length * 42))} showYAxis={false} legend={false} xAxisLabel={props.category} yAxisLabel={props.value}/></div> : <p className="genui-empty">No numeric saved rows.</p>}
      <DataTable columns={[props.category, props.value]} data={data} caption="Chart data" />
    </View>;
  },
});

const ResultLine = defineComponent({
  name: "ResultLine",
  description: "Shows a numeric series over saved x-axis values; inactive readings use triangle markers.",
  props: z.object({ resultId, title, x: column, series: z.array(column).min(1).max(8), inactive: column.optional() }),
  component: ({ props }) => {
    const data = useResult(props.resultId);
    const rows = data?.rows ?? [];
    const values = props.series.map((name) => rows.map((row) => numeric(row[name])));
    const present = values.flat().filter((n): n is number => n !== null);
    const min = Math.min(0, ...present), max = Math.max(1, ...present);
    const point = (index: number, value: number) => ({
      x: rows.length < 2 ? 320 : 46 + index * 548 / (rows.length - 1),
      y: 16 + (max === min ? 120 : (max - value) * 240 / (max - min)),
    });
    const segments = values.map((line) => {
      const output: string[] = []; let segment: string[] = [];
      line.forEach((value, index) => {
        if (value === null) { if (segment.length) output.push(segment.join(" ")); segment = []; }
        else { const p = point(index, value); segment.push(`${p.x},${p.y}`); }
      });
      if (segment.length) output.push(segment.join(" "));
      return output;
    });
    return <View title={props.title}>
      {rows.length ? <div className="genui-line-wrap"><svg className="genui-line-chart" viewBox="0 0 640 280" role="img" aria-label={`${props.title} line chart`} preserveAspectRatio="xMinYMin meet">
        <path d="M46 16V256H594" fill="none" className="genui-chart-axis"/><text x="40" y="24" textAnchor="end" className="genui-axis-label">{max}</text><text x="40" y="256" textAnchor="end" className="genui-axis-label">{min}</text>
        {segments.flatMap((lines, lineIndex) => lines.filter((s) => s.includes(" ")).map((points, i) => <polyline key={`${lineIndex}-${i}`} points={points} className={`genui-line genui-line-${lineIndex % 4}`} fill="none"/>))}
        {rows.flatMap((row, index) => values.map((line, lineIndex) => {
          const value = line[index]; if (value === null) return null;
          const p = point(index, value);
          const stopped = props.inactive && (row[props.inactive] === true || row[props.inactive] === 1);
          return stopped
            ? <g key={`${index}-${lineIndex}`}><path d={`M${p.x} ${p.y - 7} l7 13 h-14 Z`} className="genui-inactive-point"/><text x={p.x - 9} y={p.y + 4} textAnchor="end" className="genui-value-label">Stopped</text></g>
            : <circle key={`${index}-${lineIndex}`} cx={p.x} cy={p.y} r="4" className={`genui-line-point genui-line-point-${lineIndex % 4}`}/>;
        }))}
        {rows.map((row, index) => props.inactive && (row[props.inactive] === true || row[props.inactive] === 1) && values.every((line) => line[index] === null) ? <g key={`stopped-${index}`}><path d={`M${rows.length < 2 ? 320 : 46 + index * 548 / (rows.length - 1)} 249 l7 13 h-14 Z`} className="genui-inactive-point"/><text x={rows.length < 2 ? 329 : 55 + index * 548 / (rows.length - 1)} y="260" className="genui-value-label">Stopped</text></g> : null)}
        {rows.map((row, index) => rows.length <= 8 || index === 0 || index === rows.length - 1 ? <text key={index} x={rows.length < 2 ? 320 : 46 + index * 548 / (rows.length - 1)} y="276" textAnchor="middle" className="genui-axis-label">{short(display(row[props.x]), 12)}</text> : null)}
      </svg></div> : <p className="genui-empty">No saved rows.</p>}
      <p className="genui-legend">{props.series.map((name, index) => <React.Fragment key={name}><span className={`genui-legend-line genui-line-${index % 4}`}/> {name} </React.Fragment>)}{props.inactive && <><span className="genui-legend-triangle"/> Stopped reading</>}</p>
      <DataTable columns={[props.x, ...props.series, ...(props.inactive ? [props.inactive] : [])]} data={data} caption="Chart data" />
    </View>;
  },
});

const ResultMap = defineComponent({
  name: "ResultMap",
  description: "Maps saved coordinates and provides a keyboard-accessible coordinate table.",
  props: z.object({ resultId, title, lat: column, lon: column, label: column, details: fields.optional() }),
  component: ({ props }) => {
    const data = useResult(props.resultId);
    const rows = data?.rows ?? [];
    const mapRef = useRef<HTMLDivElement>(null);
    const [tileError, setTileError] = useState(false);
    useEffect(() => {
      let map: import("leaflet").Map | undefined;
      let resize: ResizeObserver | undefined;
      let cancelled = false;
      void import("leaflet").then((leaflet) => {
        if (cancelled || !mapRef.current) return;
        const L = leaflet.default;
        const points = rows.flatMap((row) => {
          const lat = numeric(row[props.lat]), lon = numeric(row[props.lon]);
          return lat !== null && lon !== null && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 ? [{ row, lat, lon }] : [];
        });
        map = L.map(mapRef.current, { scrollWheelZoom: false, worldCopyJump: true });
        const layer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }).addTo(map);
        layer.on("tileerror", () => setTileError(true));
        const markers = points.map(({ row, lat, lon }) => {
          const marker = L.circleMarker([lat, lon], { radius: 7, color: "#fff", weight: 2, fillColor: "#187363", fillOpacity: 1 }).addTo(map!);
          marker.bindPopup(`<strong>${escapeHtml(display(row[props.label]))}</strong>${(props.details ?? []).map((field) => `<br>${escapeHtml(field)}: ${escapeHtml(display(row[field]))}`).join("")}`);
          return marker;
        });
        if (markers.length === 1) map.setView(markers[0].getLatLng(), 10);
        else if (markers.length) map.fitBounds(L.featureGroup(markers).getBounds().pad(0.12));
        else map.setView([20, 0], 2);
        resize = new ResizeObserver(() => map?.invalidateSize());
        resize.observe(mapRef.current);
        requestAnimationFrame(() => map?.invalidateSize());
      }).catch(() => setTileError(true));
      return () => { cancelled = true; resize?.disconnect(); map?.remove(); };
    }, [rows, props.lat, props.lon, props.label, props.details]);
    const columns = [props.label, props.lat, props.lon, ...(props.details ?? [])];
    return <View title={props.title}>
      {tileError && <p className="genui-map-status" role="status">Map tiles could not load. Coordinates and details are available in the table.</p>}
      <div className="genui-map" ref={mapRef} aria-label="Map of saved result coordinates" />
      <DataTable columns={columns} data={data} caption="Coordinates and details" />
    </View>;
  },
});

const ResultHeatmap = defineComponent({
  name: "ResultHeatmap",
  description: "Shows saved x/y combinations; zero is distinct from a missing combination.",
  props: z.object({ resultId, title, x: column, y: column, value: column }),
  component: ({ props }) => {
    const data = useResult(props.resultId);
    const rows = data?.rows ?? [];
    const xs = [...new Set(rows.map((row) => display(row[props.x])))];
    const ys = [...new Set(rows.map((row) => display(row[props.y])))];
    const cells = new Map(rows.map((row) => [`${display(row[props.x])}\0${display(row[props.y])}`, row[props.value]]));
    const values = [...cells.values()].map(numeric).filter((n): n is number => n !== null);
    const max = Math.max(1, ...values);
    return <View title={props.title}>
      <p className="genui-legend">Value intensity: <span className="genui-heat-low">low</span> to <span className="genui-heat-high">high</span>; “—” means no saved combination, and 0 is an observed zero.</p>
      {xs.length && ys.length ? <div className="genui-grid-wrap"><table className="genui-heatmap"><caption>Heatmap values</caption><thead><tr><th scope="col">{props.y} / {props.x}</th>{xs.map((x) => <th scope="col" key={x}>{x}</th>)}</tr></thead><tbody>{ys.map((y) => <tr key={y}><th scope="row">{y}</th>{xs.map((x) => {
        const key = `${x}\0${y}`;
        const exists = cells.has(key), value = cells.get(key);
        const n = numeric(value);
        const alpha = n === null ? 0 : 0.12 + 0.68 * Math.max(0, n) / max;
        return <td key={x} className={exists ? "genui-heat-cell" : "genui-heat-unknown"} style={exists && n !== null ? { backgroundColor: `rgba(24, 115, 99, ${alpha})`, color: alpha > 0.55 ? "#fff" : "#222a30" } : undefined}>{exists ? display(value) : "—"}</td>;
      })}</tr>)}</tbody></table></div> : <p className="genui-empty">No saved rows; combinations are unknown.</p>}
      <DataTable columns={[props.x, props.y, props.value]} data={data} caption="Saved heatmap rows" />
    </View>;
  },
});

export const resultLibrary: Library = createLibrary({
  root: "AnswerLayout",
  components: [AnswerLayout, ResultCard, ResultTable, ResultBar, ResultLine, ResultMap, ResultHeatmap],
});

const parser = createParser(resultLibrary.toJSONSchema(), resultLibrary.root);

export const openuiPromptOptions = {
  preamble: "Compose a concise answer from saved results. Use only literal result IDs and column names supplied by the server.",
  additionalRules: [
    "Use only ResultCard, ResultTable, ResultBar, ResultLine, ResultMap, and ResultHeatmap inside AnswerLayout.",
    "Never invent row values, result IDs, or columns.",
    "Do not use Query, Mutation, functions, actions, reactive state, or dynamic expressions. Static component references are allowed.",
    "Use ResultLine inactive for stopped readings; use ResultMap details for useful identifying fields.",
  ],
  examples: [
    'root = AnswerLayout([status, trend, locations])\nstatus = ResultCard("R1", "Latest status", ["asset_id", "producing"])\ntrend = ResultLine("R1", "Temperature trend", "observed_at", ["wellhead_temp_c"], "inactive")\nlocations = ResultMap("R1", "Well locations", "latitude", "longitude", "asset_id", ["area"])',
    'root = AnswerLayout([compare, spread])\ncompare = ResultBar("R2", "Production by asset", "asset_id", "production_bbl")\nspread = ResultHeatmap("R2", "Production by area and day", "area", "day", "production_bbl")',
  ],
  toolCalls: false,
  bindings: false,
  builtinFunctions: false,
};

export function validateProgram(program: string, results: Results) {
  if (typeof program !== "string" || program.length > 20_000) throw new Error("Rejected OpenUI program size");
  const parsed = parser.parse(program);
  const { meta } = parsed;
  if (!parsed.root || parsed.rootExpression || meta.incomplete || meta.unresolved.length || meta.orphaned.length || meta.errors.length || parsed.queryStatements.length || parsed.mutationStatements.length || Object.keys(parsed.stateDeclarations).length) {
    throw new Error(`Rejected OpenUI program: ${JSON.stringify(meta)}`);
  }
  let nodes = 0;
  const visit = (node: unknown, depth = 1): void => {
    if (depth > 4 || ++nodes > 30 || !isNode(node) || (node as any).hasDynamicProps) throw new Error("Rejected OpenUI tree bounds, node, or dynamic expression");
    if (node.typeName === "AnswerLayout") {
      if (depth !== 1 || !Array.isArray(node.props.children) || node.props.children.length < 1 || node.props.children.length > 6) throw new Error("Invalid root layout");
      node.props.children.forEach((child) => visit(child, depth + 1)); return;
    }
    const fieldsByType: Record<string, string[]> = {
      ResultCard: node.typeName === "ResultCard" ? node.props.fields : [],
      ResultTable: node.typeName === "ResultTable" ? node.props.fields : [],
      ResultBar: node.typeName === "ResultBar" ? [node.props.category, node.props.value] : [],
      ResultLine: node.typeName === "ResultLine" ? [node.props.x, ...(node.props.series ?? []), ...(node.props.inactive ? [node.props.inactive] : [])] : [],
      ResultMap: node.typeName === "ResultMap" ? [node.props.lat, node.props.lon, node.props.label, ...(node.props.details ?? [])] : [],
      ResultHeatmap: node.typeName === "ResultHeatmap" ? [node.props.x, node.props.y, node.props.value] : [],
    };
    if (!Object.hasOwn(fieldsByType, node.typeName)) throw new Error("Unsupported OpenUI component");
    if ((node.typeName === "ResultCard" || node.typeName === "ResultTable") && (!Array.isArray(node.props.fields) || node.props.fields.length < 1 || node.props.fields.length > 20)) throw new Error("Invalid field selection");
    if (node.typeName === "ResultLine" && (!Array.isArray(node.props.series) || node.props.series.length < 1 || node.props.series.length > 8)) throw new Error("Invalid line series selection");
    if (node.typeName === "ResultMap" && node.props.details !== undefined && (!Array.isArray(node.props.details) || node.props.details.length > 20)) throw new Error("Invalid map detail selection");
    const resultId = node.props.resultId;
    if (typeof resultId !== "string" || resultId.length < 1 || resultId.length > 80 || typeof node.props.title !== "string" || !node.props.title.length || node.props.title.length > 160 || fieldsByType[node.typeName].some((field) => typeof field !== "string" || field.length < 1 || field.length > 80)) throw new Error("Invalid result view arguments");
    if (!Object.hasOwn(results, resultId)) throw new Error(`Unknown result: ${resultId}`);
    const data = results[resultId];
    if (!data || !Array.isArray(data.columns) || !Array.isArray(data.rows)) throw new Error(`Unknown result or column: ${resultId}`);
    if (node.typeName === "ResultCard" && data.rows.length !== 1) throw new Error("ResultCard requires exactly one saved row");
    if (fieldsByType[node.typeName].some((field) => !data.columns.includes(field))) throw new Error(`Unknown result column: ${resultId}`);
  };
  visit(parsed.root);
  return parsed;
}

function useResult(id: string) { return useContext(ResultsContext)[id]; }
function oneRow(id: string) { const data = useResult(id); return { data, row: data?.rows.length === 1 ? data.rows[0] : undefined }; }
function View({ title: heading, children }: { title: string; children: React.ReactNode }) { return <section className="genui-view"><h3>{heading}</h3>{children}</section>; }
function DataTable({ columns, data, caption = "" }: { columns: string[]; data?: ResultData; caption?: string }) {
  return <div className="genui-table-wrap"><table className="genui-data-table"><caption>{caption}</caption><thead><tr>{columns.map((col) => <th scope="col" key={col}>{col}</th>)}</tr></thead><tbody>{(data?.rows ?? []).map((row, i) => <tr key={i}>{columns.map((col) => <td key={col}>{display(row[col])}</td>)}</tr>)}</tbody></table>{!data?.rows.length && <p className="genui-empty">No saved rows.</p>}</div>;
}
function display(value: unknown) { return value === null || value === undefined ? "Unknown" : typeof value === "object" ? JSON.stringify(value) : String(value); }
function numeric(value: unknown) { return typeof value === "number" && Number.isFinite(value) ? value : null; }
function short(value: string, limit: number) { return value.length > limit ? `${value.slice(0, limit - 1)}…` : value; }
function escapeHtml(value: string) { return value.replace(/[&<>"']/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[char]!); }
function isNode(value: unknown): value is { type: "element"; typeName: string; props: Record<string, any>; partial: boolean } {
  return !!value && typeof value === "object" && (value as any).type === "element";
}
