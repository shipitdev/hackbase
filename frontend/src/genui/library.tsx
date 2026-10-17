import React, { createContext, useContext } from "react";
import { createLibrary, createParser, defineComponent, type Library } from "@openuidev/react-lang";
import { openuiLibrary } from "@openuidev/react-ui";
import { z } from "zod/v4";

export type ResultData = { columns: string[]; rows: Record<string, unknown>[] };
export type Results = Record<string, ResultData>;

const ResultsContext = createContext<Results>({});
export const ResultsProvider = ResultsContext.Provider;

const resultId = z.string().min(1).max(80);
const fields = z.array(z.string().min(1).max(80)).min(1).max(20);
const UiNode = z.union([z.lazy(() => ResultCard.ref), z.lazy(() => ResultTable.ref)]);

const AnswerLayout = defineComponent({
  name: "AnswerLayout",
  description: "Root layout that composes result-backed cards and tables.",
  props: z.object({ children: z.array(UiNode).min(1).max(6) }),
  component: ({ props, renderNode }) => <div className="answer-layout">{renderNode(props.children)}</div>,
});

const ResultCard = defineComponent({
  name: "ResultCard",
  description: "Shows selected fields from one row in a server-saved result.",
  props: z.object({ resultId, title: z.string().min(1).max(160), fields }),
  component: ({ props, renderNode }) => {
    const results = useContext(ResultsContext);
    const data = results[props.resultId];
    const row = data?.rows.length === 1 ? data.rows[0] : undefined;
    const children = [
      textNode("TextContent", { text: props.title }),
      ...props.fields.map((field) =>
        textNode("TextContent", { text: `${field}: ${String(row?.[field] ?? "Unknown")}` }),
      ),
    ];
    const BuiltinCard = openuiLibrary.components.Card.component;
    const renderBuiltin = (nodes: unknown): React.ReactNode => {
      const Text = openuiLibrary.components.TextContent.component;
      const list = Array.isArray(nodes) ? nodes : [nodes];
      return list.map((node, index) =>
        isNode(node, "TextContent")
          ? React.createElement(Text, { key: index, props: node.props, renderNode })
          : null,
      );
    };
    return React.createElement(BuiltinCard, {
      props: { children, variant: "card", direction: "column" },
      renderNode: renderBuiltin,
    });
  },
});

const ResultTable = defineComponent({
  name: "ResultTable",
  description: "Shows selected columns from a server-saved result.",
  props: z.object({ resultId, title: z.string().min(1).max(160), fields }),
  component: ({ props, renderNode }) => {
    const results = useContext(ResultsContext);
    const data = results[props.resultId];
    const columns = props.fields.map((field) => ({
      type: "element" as const,
      typeName: "Col",
      partial: false,
      props: {
        label: field,
        data: data?.rows.map((row) => row[field] ?? null) ?? [],
      },
    }));
    const BuiltinCard = openuiLibrary.components.Card.component;
    const BuiltinTable = openuiLibrary.components.Table.component;
    const renderBuiltin = (nodes: unknown): React.ReactNode => {
      const list = Array.isArray(nodes) ? nodes : [nodes];
      return list.map((node, index) => {
        if (!isNode(node)) return null;
        const definition = openuiLibrary.components[node.typeName];
        if (!definition) return null;
        return React.createElement(definition.component, {
          key: index,
          props: node.props,
          renderNode: renderBuiltin,
        });
      });
    };
    return React.createElement(
      BuiltinCard,
      {
        props: {
          children: [
            textNode("TextContent", { text: props.title }),
            { type: "element", typeName: "Table", partial: false, props: { columns } },
          ],
          variant: "card",
          direction: "column",
        },
        renderNode: (nodes: unknown) => {
          const list = Array.isArray(nodes) ? nodes : [nodes];
          return list.map((node, index) => {
            if (isNode(node, "Table")) {
              return React.createElement(BuiltinTable, { key: index, props: node.props, renderNode });
            }
            if (isNode(node, "TextContent")) {
              const Text = openuiLibrary.components.TextContent.component;
              return React.createElement(Text, { key: index, props: node.props, renderNode });
            }
            return null;
          });
        },
      },
    );
  },
});

export const resultLibrary: Library = createLibrary({
  root: "AnswerLayout",
  components: [AnswerLayout, ResultCard, ResultTable],
});

const parser = createParser(resultLibrary.toJSONSchema(), resultLibrary.root);

export const openuiPromptOptions = {
  preamble: "Compose a concise answer from saved results. Use only literal result IDs and column names supplied by the server.",
  additionalRules: [
    "Use only ResultCard and ResultTable inside AnswerLayout.",
    "Never invent row values, result IDs, or columns.",
    "Do not use Query, Mutation, functions, actions, variables, or dynamic expressions.",
  ],
  examples: [
    'root = AnswerLayout([status, detail])\nstatus = ResultCard("R1", "Latest status", ["asset_id", "producing"])\ndetail = ResultTable("R1", "Inspection detail", ["asset_id", "wellhead_temp_c"])',
  ],
  toolCalls: false,
  bindings: false,
  builtinFunctions: false,
};

export function validateProgram(program: string, results: Results) {
  if (typeof program !== "string" || program.length > 20_000) throw new Error("Rejected OpenUI program size");
  const parsed = parser.parse(program);
  const { meta } = parsed;
  if (
    !parsed.root ||
    parsed.rootExpression ||
    meta.incomplete ||
    meta.unresolved.length ||
    meta.orphaned.length ||
    meta.errors.length ||
    parsed.queryStatements.length ||
    parsed.mutationStatements.length ||
    Object.keys(parsed.stateDeclarations).length
  ) {
    throw new Error(`Rejected OpenUI program: ${JSON.stringify(meta)}`);
  }
  let nodes = 0;
  let views = 0;
  const visit = (node: unknown, depth = 1): void => {
    if (depth > 4 || ++nodes > 30 || !isNode(node) || (node as any).hasDynamicProps) {
      throw new Error("Rejected OpenUI tree bounds, node, or dynamic expression");
    }
    if (node.typeName === "AnswerLayout") {
      if (
        depth !== 1 ||
        !Array.isArray(node.props.children) ||
        node.props.children.length < 1 ||
        node.props.children.length > 6
      ) throw new Error("Invalid root layout");
      node.props.children.forEach((child) => visit(child, depth + 1));
      return;
    }
    if (node.typeName !== "ResultCard" && node.typeName !== "ResultTable") throw new Error("Unsupported OpenUI component");
    if (++views > 6) throw new Error("Too many result views");
    const { resultId, title, fields: selected } = node.props as {
      resultId: unknown;
      title: unknown;
      fields: unknown;
    };
    if (
      typeof resultId !== "string" || resultId.length < 1 || resultId.length > 80 ||
      typeof title !== "string" || title.length < 1 || title.length > 160 ||
      !Array.isArray(selected) || selected.length < 1 || selected.length > 20 ||
      selected.some((field) => typeof field !== "string" || field.length < 1 || field.length > 80)
    ) throw new Error("Invalid result view arguments");
    if (!Object.hasOwn(results, resultId)) throw new Error(`Unknown result: ${resultId}`);
    const data = results[resultId];
    if (!data || !Array.isArray(data.columns) || !Array.isArray(data.rows)) {
      throw new Error(`Unknown result or column: ${resultId}`);
    }
    if (node.typeName === "ResultCard" && data.rows.length !== 1) {
      throw new Error("ResultCard requires exactly one saved row");
    }
    if (selected.some((field) => !data.columns.includes(field))) throw new Error(`Unknown result column: ${resultId}`);
  };
  visit(parsed.root);
  return parsed;
}

function textNode(typeName: string, props: Record<string, unknown>) {
  return { type: "element", typeName, props, partial: false };
}

function isNode(value: unknown, typeName?: string): value is { type: "element"; typeName: string; props: Record<string, any>; partial: boolean } {
  return !!value && typeof value === "object" && (value as any).type === "element" && (!typeName || (value as any).typeName === typeName);
}

