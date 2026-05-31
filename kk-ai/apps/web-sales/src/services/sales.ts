export interface Script {
  id: string;
  title: string;
  content: string;
  category: string;
  tags: string[];
  scenario: string;
  conversion_rate: number;
  usage_count: number;
  created_at: string;
}

const BASE = "/v1/sales";

export async function querySales(
  customer_question: string,
  user_id?: string,
  scenario?: string,
) {
  const res = await fetch(`${BASE}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_question, user_id, scenario }),
  });
  if (!res.ok) throw new Error("查询失败");
  return res.json();
}

export async function startRoleplay(
  customer_type: string,
  scenario?: string,
  product?: string,
) {
  const res = await fetch(`${BASE}/roleplay/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ customer_type, scenario, product }),
  });
  if (!res.ok) throw new Error("启动陪练失败");
  return res.json();
}

export async function chatRoleplay(session_id: string, message: string) {
  const res = await fetch(`${BASE}/roleplay/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id, message }),
  });
  if (!res.ok) throw new Error("对话失败");
  return res.json();
}

export async function evaluateRoleplay(session_id: string) {
  const res = await fetch(`${BASE}/roleplay/evaluate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id }),
  });
  if (!res.ok) throw new Error("评估失败");
  return res.json();
}

export async function listScripts(params?: {
  category?: string;
  q?: string;
  page?: number;
  page_size?: number;
}) {
  const sp = new URLSearchParams();
  if (params?.category) sp.set("category", params.category);
  if (params?.q) sp.set("q", params.q);
  sp.set("page", String(params?.page || 1));
  sp.set("page_size", String(params?.page_size || 20));
  const res = await fetch(`${BASE}/scripts?${sp.toString()}`);
  if (!res.ok) throw new Error("加载话术库失败");
  return res.json();
}

export async function createScript(data: Omit<Script, "id" | "created_at">) {
  const res = await fetch(`${BASE}/scripts`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) throw new Error("创建话术失败");
  return res.json();
}

export async function deleteScript(id: string) {
  const res = await fetch(`${BASE}/scripts/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("删除失败");
}
