const BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export function authHeaders(): Record<string, string> {
  const token = typeof window !== "undefined" ? localStorage.getItem("nra_access") : null;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function handle<T>(res: Response): Promise<T> {
  if (res.ok) return res.json();
  const txt = await res.text();
  let msg = txt;
  try { const j = JSON.parse(txt); msg = j.detail || JSON.stringify(j); } catch {}
  throw new Error(msg || `HTTP ${res.status}`);
}

export async function apiRegister(payload: { email: string; password: string; age: number; sex: string; }) {
  const res = await fetch(`${BASE}/auth/register`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
  return handle<{ access_token: string; refresh_token: string }>(res);
}

export async function apiLogin(payload: { email: string; password: string; }) {
  const res = await fetch(`${BASE}/auth/login`, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(payload) });
  return handle<{ access_token: string; refresh_token: string }>(res);
}

export async function apiCapabilityCreate(payload: { date: string; comfortable_distance_m: number; comfortable_time_sec: number; }) {
  const headers: HeadersInit = { "content-type": "application/json", ...authHeaders() };
  const res = await fetch(`${BASE}/capability`, { method: "POST", headers, body: JSON.stringify(payload) });
  return handle<{ id: string } & Record<string, any>>(res);
}

export async function apiGoalCreate(payload: { distance_m: number; target_time_sec?: number | null; target_date: string; }) {
  const headers: HeadersInit = { "content-type": "application/json", ...authHeaders() };
  const res = await fetch(`${BASE}/goals`, { method: "POST", headers, body: JSON.stringify(payload) });
  return handle<{ id: string } & Record<string, any>>(res);
}

export async function apiFeasibility(goalId: string) {
  const headers: HeadersInit = { ...authHeaders() };
  const res = await fetch(`${BASE}/goals/${goalId}/feasibility`, { method: "POST", headers });
  return handle<{ feasible: boolean; reasons: string[]; tradeoffs: Array<{ lever: string; recommendation: any }>; }>(res);
}

export async function apiGeneratePlan(goalId: string) {
  const headers: HeadersInit = { ...authHeaders() };
  const res = await fetch(`${BASE}/plans/goals/${goalId}/generate-plan`, { method: "POST", headers });
  return handle<{ id: string } & Record<string, any>>(res);
}

export async function apiCurrentPlan() {
  const headers: HeadersInit = { ...authHeaders() };
  const res = await fetch(`${BASE}/plans/current`, { headers });
  return handle<{ id: string; workouts: any[] }>(res);
}
