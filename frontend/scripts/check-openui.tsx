import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Renderer } from "@openuidev/react-lang";
import { openuiPromptOptions, resultLibrary, ResultsProvider, validateProgram, type Results } from "../src/genui/library.tsx";

const root = resolve(import.meta.dirname, "../src/genui/generated");
const schemaFile = resolve(root, "schema.json");
const promptFile = resolve(root, "system-prompt.txt");
const schema = resultLibrary.toJSONSchema();
const prompt = resultLibrary.prompt(openuiPromptOptions);
if (process.argv.includes("--write")) {
  await mkdir(root, { recursive: true });
  await writeFile(schemaFile, `${JSON.stringify(schema, null, 2)}\n`);
  await writeFile(promptFile, `${prompt.trim()}\n`);
} else {
  assert.equal(await readFile(schemaFile, "utf8"), `${JSON.stringify(schema, null, 2)}\n`, "generated schema drift; run npm run check:openui -- --write");
  assert.equal(await readFile(promptFile, "utf8"), `${prompt.trim()}\n`, "generated prompt drift; run npm run check:openui -- --write");
}

const columns = ["asset_id", "producing", "wellhead_temp_c", "observed_at", "inactive", "area", "latitude", "longitude", "day", "volume"];
const rows = [
  { asset_id: "FICTIONAL-01", producing: true, wellhead_temp_c: 0, observed_at: "2026-10-01", inactive: false, area: "East", latitude: 19.1, longitude: 72.8, day: "Oct 1", volume: 0 },
  { asset_id: "FICTIONAL-02", producing: false, wellhead_temp_c: null, observed_at: "2026-10-02", inactive: 1, area: "East", latitude: 20, longitude: 73, day: "Oct 2", volume: 4 },
  { asset_id: "FICTIONAL-03", producing: true, wellhead_temp_c: 8, observed_at: "2026-10-03", inactive: false, area: "West", latitude: 21, longitude: 74, day: "Oct 3", volume: -8 },
];
const results: Results = {
  "R-fixture": { columns, rows },
  "R-card": { columns, rows: [rows[0]] },
};
const valid = `root = AnswerLayout([status, readings, production, temperature, locations, spread])
status = ResultCard("R-card", "Current state", ["asset_id", "producing"])
readings = ResultTable("R-fixture", "Saved readings", ["asset_id", "wellhead_temp_c"])
production = ResultBar("R-fixture", "Values by asset", "asset_id", "volume")
temperature = ResultLine("R-fixture", "Temperature trend", "observed_at", ["wellhead_temp_c", "volume"], "inactive")
locations = ResultMap("R-fixture", "Well locations", "latitude", "longitude", "asset_id", ["area"])
spread = ResultHeatmap("R-fixture", "Values by area and day", "area", "day", "volume")`;
const parsed = validateProgram(valid, results);
assert.equal(parsed.root?.typeName, "AnswerLayout");
function rejected(program: string, why: string) { assert.throws(() => validateProgram(program, results), why); }
rejected(`root = AnswerLayout([bad])\nbad = ResultCard("R-fixture", "Invented", ["asset_id"], "invented-row-prop")`, "excess props are rejected by official parser");
rejected(`root = AnswerLayout([bad])\nbad = ResultTable("R-fixture", "Invented", ["not-a-column"])`, "unissued columns are rejected");
rejected(`root = AnswerLayout([bad])\nbad = ResultCard("R-card", "Empty", [])`, "empty selections are rejected");
rejected(`root = AnswerLayout([bad])\nbad = ResultTable("missing", "Unknown", ["asset_id"])`, "unknown result IDs are rejected");
rejected(`root = AnswerLayout([bad])\nbad = ResultTable("toString", "Inherited key", ["asset_id"])`, "inherited result keys are rejected");
rejected(valid + " ".repeat(20_000), "oversized programs are rejected");
rejected(`query = Query("run_sql", {})\nroot = AnswerLayout([status])\nstatus = ResultCard("R-card", "Current state", ["asset_id"])`, "Query programs are rejected");
rejected(`mutation = Mutation("remember", {})\nroot = AnswerLayout([status])\nstatus = ResultCard("R-card", "Current state", ["asset_id"])`, "Mutation programs are rejected");
rejected(`root = AnswerLayout([status])\n$show = true\nstatus = ResultCard("R-card", "Current state", ["asset_id"])`, "state declarations are rejected");
rejected(`root = $show ? AnswerLayout([status]) : AnswerLayout([status])\nstatus = ResultCard("R-card", "Current state", ["asset_id"])`, "dynamic roots are rejected");
rejected(`root = AnswerLayout([status])\nstatus = ResultCard("R-card", "Count " + @Count([1, 2]), ["asset_id"])`, "function props are rejected");
rejected(`root = AnswerLayout([status])\nstatus = ResultCard("R-card", "Current state", ["asset_id"])\naction = Action([@OpenUrl("https://example.invalid")])`, "orphan action programs are rejected");
assert.throws(() => validateProgram(`root = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Ambiguous", ["asset_id"])`, results), /exactly one saved row/);

const html = renderToStaticMarkup(<ResultsProvider value={results}><Renderer library={resultLibrary} response={valid}/></ResultsProvider>);
assert.match(html, /FICTIONAL-01/);
assert.match(html, /Temperature trend/);
assert.match(html, /Values by asset/);
assert.match(html, /bar-chart-container/, "native OpenUI bar chart is rendered");
assert.match(html, /Coordinates and details/);
assert.match(html, /Heatmap values/);
assert.match(html, /genui-inactive-point/, "inactive readings have a separate marker shape");
assert.match(html, /genui-line-0/, "line series have their own visual identity");
assert.doesNotMatch(html, /class="genui-line genui-line-0"/, "missing line readings leave a gap in that series");
assert.match(html, /Stopped reading/);
assert.match(html, /Unknown/, "null readings remain unknown");
assert.match(html, />0</, "observed zero remains explicit");
assert.match(html, /—/, "unobserved heatmap combinations remain unknown");
assert.doesNotMatch(html, /width="-/, "negative bar values never create negative-width SVG bars");
assert.doesNotMatch(html, /leaflet-container/, "map waits for browser mount and is SSR-safe");

const bridge = spawnSync(process.execPath, ["--import", "tsx", "scripts/validate-openui.tsx"], {
  input: JSON.stringify({ program: valid, results }), encoding: "utf8", timeout: 10_000,
});
assert.equal(bridge.status, 0, bridge.stderr);
const views = JSON.parse(bridge.stdout) as Array<{ type: string; result_id: string; title: string; mapping: Record<string, unknown> }>;
assert.deepEqual(views.map((view) => view.type), ["card", "table", "bar", "line", "map", "heatmap"]);
assert.deepEqual(views[2].mapping, { category: "asset_id", value: "volume" });
assert.deepEqual(views[3].mapping, { x: "observed_at", series: ["wellhead_temp_c", "volume"], inactive: "inactive" });
assert.deepEqual(views[4].mapping, { lat: "latitude", lon: "longitude", label: "asset_id", details: ["area"] });
assert.deepEqual(views[5].mapping, { x: "area", y: "day", value: "volume" });
const optionalTail = `root = AnswerLayout([trend, places])\ntrend = ResultLine("R-fixture", "Trend", "observed_at", ["wellhead_temp_c"])\nplaces = ResultMap("R-fixture", "Places", "latitude", "longitude", "asset_id")`;
assert.equal(validateProgram(optionalTail, results).root?.typeName, "AnswerLayout", "optional trailing arguments can be omitted");

const hostile: Results = { "R-html": { columns: ["asset_id"], rows: [{ asset_id: "<img src=x onerror=alert(1)>" }] } };
const hostileProgram = `root = AnswerLayout([status])\nstatus = ResultCard("R-html", "<script>alert(1)</script>", ["asset_id"])`;
const hostileHtml = renderToStaticMarkup(<ResultsProvider value={hostile}><Renderer library={resultLibrary} response={hostileProgram}/></ResultsProvider>);
assert.doesNotMatch(hostileHtml, /<script>|<img /);
assert.match(hostileHtml, /&lt;script&gt;/);
assert.match(hostileHtml, /&lt;img/);
console.log("OpenUI six-view check passed: generated schema/prompt, parser guards, SSR, zero/unknown/inactive behavior, and canonical bridge mappings.");

const exampleColumns = ["asset_id", "producing", "observed_at", "wellhead_temp_c", "inactive", "latitude", "longitude", "area", "day", "production_bbl"];
for (const example of openuiPromptOptions.examples) {
  assert.doesNotThrow(() => validateProgram(example, {
    R1: { columns: exampleColumns, rows: [{}] },
    R2: { columns: exampleColumns, rows: [{}] },
  }), "Published prompt examples must parse against their issued fixture columns");
}
