import { validateProgram, type Results } from "../src/genui/library.tsx";

const chunks: Buffer[] = [];
let size = 0;
for await (const chunk of process.stdin) {
  size += chunk.length;
  if (size > 64_000) throw new Error("Input too large");
  chunks.push(chunk);
}
try {
  const input = JSON.parse(Buffer.concat(chunks).toString("utf8")) as {
    program: string;
    results: Results;
  };
  const parsed = validateProgram(input.program, input.results);
  const views: Array<{ type: string; result_id: string; title: string; mapping: Record<string, string | string[]> }> = [];
  const visit = (node: any) => {
    if (node.typeName === "AnswerLayout") return node.props.children.forEach(visit);
    const types: Record<string, string> = {
      ResultCard: "card", ResultTable: "table", ResultBar: "bar", ResultLine: "line",
      ResultMap: "map", ResultHeatmap: "heatmap",
    };
    const type = types[node.typeName];
    let mapping: Record<string, string | string[]>;
    switch (node.typeName) {
      case "ResultCard": mapping = { fields: node.props.fields }; break;
      case "ResultTable": mapping = { columns: node.props.fields }; break;
      case "ResultBar": mapping = { category: node.props.category, value: node.props.value }; break;
      case "ResultLine": mapping = { x: node.props.x, series: node.props.series, ...(node.props.inactive ? { inactive: node.props.inactive } : {}) }; break;
      case "ResultMap": mapping = { lat: node.props.lat, lon: node.props.lon, label: node.props.label, ...(node.props.details ? { details: node.props.details } : {}) }; break;
      case "ResultHeatmap": mapping = { x: node.props.x, y: node.props.y, value: node.props.value }; break;
      default: throw new Error("Unsupported OpenUI component");
    }
    views.push({
      type,
      result_id: node.props.resultId,
      title: node.props.title,
      mapping,
    });
  };
  visit(parsed.root);
  const output = JSON.stringify(views);
  if (Buffer.byteLength(output) > 16_000) throw new Error("Output too large");
  process.stdout.write(output);
} catch {
  process.stderr.write("OpenUI validation failed\n");
  process.exitCode = 1;
}
