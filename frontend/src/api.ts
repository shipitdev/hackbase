import type { Answer, Evidence, Health, Message, Thread, User } from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new Error(data?.error?.message ?? `Request failed (${response.status})`);
  return data as T;
}

export const api = {
  health: () => request<Health>("/health"),
  users: async () => (await request<{ users: User[] }>("/users")).users,
  threads: async (userId: string) => (await request<{ threads: Thread[] }>(`/threads?user_id=${encodeURIComponent(userId)}`)).threads,
  messages: async (userId: string, threadId: string) => (await request<{ messages: Message[] }>(`/threads/${encodeURIComponent(threadId)}/messages?user_id=${encodeURIComponent(userId)}`)).messages,
  newThread: (user_id: string) => request<Thread>("/threads", { method: "POST", body: JSON.stringify({ user_id }) }),
  chat: (body: { request_id: string; user_id: string; thread_id: string; text: string }) => request<Answer>("/chat", { method: "POST", body: JSON.stringify(body) }),
  evidence: async (userId: string, reference: string) => (await request<{ evidence: Evidence[] }>(`/evidence/${encodeURIComponent(reference)}?user_id=${encodeURIComponent(userId)}`)).evidence[0],
};
