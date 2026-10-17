import assert from "node:assert/strict";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { Renderer } from "@openuidev/react-lang";
import {
  openuiPromptOptions,
  resultLibrary,
  ResultsProvider,
  validateProgram,
  type Results,
} from "../src/genui/library.tsx";

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

const results: Results = {
  "R-fixture": {
    columns: ["asset_id", "producing", "wellhead_temp_c"],
    rows: [{ asset_id: "FICTIONAL-01", producing: true, wellhead_temp_c: 41 }],
  },
};
const valid = `root = AnswerLayout([status, readings])
status = ResultCard("R-fixture", "Current state", ["asset_id", "producing"])
readings = ResultTable("R-fixture", "Saved readings", ["asset_id", "wellhead_temp_c"])`;
const parsed = validateProgram(valid, results);
assert.equal(parsed.root?.typeName, "AnswerLayout");

function rejected(program: string, why: string) {
  assert.throws(() => validateProgram(program, results), undefined, why);
}

rejected(
  `root = AnswerLayout([bad])\nbad = ResultCard("R-fixture", "Invented", ["asset_id"], "invented-row-prop")`,
  "excess props are rejected by the official parser",
);
rejected(
  `root = AnswerLayout([bad])\nbad = ResultTable("R-fixture", "Invented", ["not-a-column"])`,
  "columns outside the server result are rejected",
);
rejected(
  `root = AnswerLayout([bad])\nbad = ResultCard("R-fixture", "Empty", [])`,
  "empty field selections are rejected",
);
rejected(
  `root = AnswerLayout([bad])\nbad = ResultCard("missing", "Unknown", ["asset_id"])`,
  "unknown result IDs are rejected",
);
rejected(
  `root = AnswerLayout([bad])\nbad = ResultCard("toString", "Inherited key", ["asset_id"])`,
  "inherited object keys are not accepted as server result IDs",
);
rejected(
  valid + " ".repeat(20_000),
  "oversized OpenUI programs are rejected before parsing",
);
const multirow: Results = {
  "R-fixture": { ...results["R-fixture"], rows: [results["R-fixture"].rows[0], results["R-fixture"].rows[0]] },
};
assert.throws(
  () => validateProgram(`root = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Ambiguous", ["asset_id"])`, multirow),
  /exactly one saved row/,
);
rejected(
  `query = Query("run_sql", {})\nroot = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Current state", ["asset_id"])`,
  "Query programs are rejected",
);
rejected(
  `mutation = Mutation("remember", {})\nroot = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Current state", ["asset_id"])`,
  "Mutation programs are rejected",
);
rejected(
  `root = AnswerLayout([status])\n$show = true\nstatus = ResultCard("R-fixture", "Current state", ["asset_id"])`,
  "state declarations are rejected",
);
rejected(
  `root = $show ? AnswerLayout([status]) : AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Current state", ["asset_id"])`,
  "dynamic roots are rejected",
);
rejected(
  `root = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Count " + @Count([1, 2]), ["asset_id"])`,
  "function expressions in component props are rejected",
);
rejected(
  `root = AnswerLayout([status])\nstatus = ResultCard("R-fixture", "Current state", ["asset_id"])\naction = Action([@OpenUrl("https://example.invalid")])`,
  "unreachable action programs are rejected",
);

const html = renderToStaticMarkup(
  <ResultsProvider value={results}>
    <Renderer library={resultLibrary} response={valid} />
  </ResultsProvider>,
);
assert.match(html, /FICTIONAL-01/);
assert.match(html, /41/);
assert.match(html, /producing: true/);
assert.match(html, /Current state/);
assert.match(html, /Saved readings/);
const hostile: Results = {
  "R-html": {
    columns: ["asset_id"],
    rows: [{ asset_id: "<img src=x onerror=alert(1)>" }],
  },
};
const hostileProgram = `root = AnswerLayout([status])\nstatus = ResultCard("R-html", "<script>alert(1)</script>", ["asset_id"])`;
const hostileHtml = renderToStaticMarkup(
  <ResultsProvider value={hostile}>
    <Renderer library={resultLibrary} response={hostileProgram} />
  </ResultsProvider>,
);
assert.doesNotMatch(hostileHtml, /<script>|<img /);
assert.match(hostileHtml, /&lt;script&gt;/);
assert.match(hostileHtml, /&lt;img/);
console.log("OpenUI P0 passed: generated schema/prompt, official parser restrictions, and SSR result-backed Card/Table values.");
