import type {
  Agent, DepartmentSummary, OpportunityPipelineData,
  RevenueReport, KPIs, DashboardData, Lesson,
} from '@/types';

const BASE = typeof window !== 'undefined' ? '' : (process.env.API_URL || 'http://localhost:8000');

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`, { cache: 'no-store' });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: body ? { 'Content-Type': 'application/json' } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) throw new Error(`API error ${res.status}: ${path}`);
  return res.json() as Promise<T>;
}

// ─── Agents ──────────────────────────────────────────────────────────────────

export const agentsApi = {
  list:    ()     => get<Agent[]>('/api/agents/'),
  get:     (name: string) => get<Agent>(`/api/agents/${name}`),
  inbox:   (name: string) => get<{ messages: unknown[] }>(`/api/agents/${name}/inbox`),
  depts:   ()     => get<Record<string, DepartmentSummary>>('/api/agents/departments/summary'),
  task:    (body: { agent_name: string; task_type: string; payload?: Record<string, unknown> }) =>
             post<{ status: string }>('/api/agents/task', body),
};

// ─── Opportunities ────────────────────────────────────────────────────────────

export const opportunitiesApi = {
  pipeline:    () => get<OpportunityPipelineData>('/api/opportunities/pipeline'),
  leaderboard: () => get<{ leaderboard: unknown[] }>('/api/opportunities/leaderboard'),
  threshold:   () => get<{ threshold: number }>('/api/opportunities/threshold'),
};

// ─── Revenue ──────────────────────────────────────────────────────────────────

export const revenueApi = {
  summary:       () => get<RevenueReport>('/api/revenue/summary'),
  kpis:          () => get<KPIs>('/api/revenue/kpis'),
  entries:       (limit = 50) => get<{ entries: unknown[]; count: number }>(`/api/revenue/entries?limit=${limit}`),
  record:        (body: { amount: number; entry_type: string; source: string }) =>
                   post<unknown>('/api/revenue/record', body),
  optimisations: () => get<unknown>('/api/revenue/optimisations'),
};

// ─── Memory ───────────────────────────────────────────────────────────────────

export const memoryApi = {
  lessons:  (limit = 50) => get<{ lessons: Lesson[]; count: number }>(`/api/memory/lessons?limit=${limit}`),
  insights: () => get<{ insights: unknown[] }>('/api/memory/knowledge/insights'),
  snapshot: () => get<Record<string, number>>('/api/memory/short-term'),
  query:    (query: string) => post<{ results: unknown[] }>('/api/memory/query', { query }),
};

// ─── System ───────────────────────────────────────────────────────────────────

export const systemApi = {
  dashboard:  () => get<DashboardData>('/api/system/dashboard'),
  startCycle: () => post<{ status: string }>('/api/system/cycle/start'),
  logs:       (limit = 20) => get<{ logs: unknown[] }>(`/api/system/logs?limit=${limit}`),
  config:     () => get<Record<string, unknown>>('/api/system/config'),
  health:     () => get<{ status: string }>('/health'),
};
