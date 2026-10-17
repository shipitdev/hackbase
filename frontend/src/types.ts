export type User = { user_id: string; name: string; role: string; team_id?: string | null };
export type Thread = { thread_id: string; title: string; created_at: string };
export type Evidence = { id?: string; reference?: string; kind?: string; title?: string; source_path?: string; content?: unknown; metadata?: Record<string, unknown> };
export type SavedResult = {
  result_id?: string;
  columns: { name: string; type?: string; label?: string; unit?: string }[];
  rows: Record<string, unknown>[];
  complete?: boolean;
  truncated?: boolean;
  limitations?: string[];
  analysis_date?: string;
  knowledge_revision?: number;
};
export type ComponentV1 = { id: string; type: string; title: string; result_id: string; mapping: Record<string, string | string[]> };
export type Answer = {
  request_id?: string; message_id?: string; thread_id?: string; analysis_date?: string;
  status?: "complete" | "partial"; answer: string; ui_format?: string; ui_version?: number;
  ui?: string | null; results?: Record<string, SavedResult>; components?: ComponentV1[];
  citations?: Evidence[]; conflicts?: { claim?: string; status?: string; evidence_refs?: string[] }[];
  limitations?: string[];
};
export type Message = { message_id: string; role: "user" | "assistant"; text: string; created_at: string; answer?: Answer | null };
export type Health = { ready: boolean; chat_ready: boolean; analysis_date: string; dataset_version?: string | null; model?: string };
