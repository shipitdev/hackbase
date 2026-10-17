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
  const views: Array<{ type: string; result_id: string; title: string; mapping: { fields?: string[]; columns?: string[] } }> = [];
  const visit = (node: any) => {
    if (node.typeName === "AnswerLayout") return node.props.children.forEach(visit);
    const type = node.typeName === "ResultCard" ? "card" : "table";
    views.push({
      type,
      result_id: node.props.resultId,
      title: node.props.title,
      mapping: type === "card" ? { fields: node.props.fields } : { columns: node.props.fields },
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
