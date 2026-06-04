// ─── Agents ───────────────────────────────────────────────────────────────────

export type AgentStatus = 'idle' | 'running' | 'blocked' | 'error' | 'not_started' | 'stopped';

export interface Agent {
  name: string;
  department: string;
  status: AgentStatus;
  tasks_completed: number;
  tasks_failed: number;
  last_active: string | null;
  current_task: string | null;
  started_at?: string;
}

export type Department = 'executive' | 'research' | 'strategy' | 'execution' | 'finance' | 'self_improvement';

export interface DepartmentSummary {
  agents: string[];
  total: number;
  running: number;
  idle: number;
  error: number;
}

// ─── Opportunities ────────────────────────────────────────────────────────────

export interface Opportunity {
  title: string;
  name?: string;
  description: string;
  category: string;
  overall_score: number;
  profit_potential: number;
  difficulty: number;
  startup_cost: number;
  time_required: number;
  automation_potential: number;
  scalability: number;
  risk_level: number;
  status: 'discovered' | 'analyzed' | 'approved' | 'executing' | 'completed' | 'rejected';
  estimated_monthly_revenue_usd?: number;
  estimated_startup_cost_usd?: number;
  income_potential?: string;
  source_agent?: string;
  created_at?: string;
}

export interface OpportunityPipelineData {
  pipeline: {
    approved:  { count: number; items: Opportunity[] };
    qualified: { count: number; items: Opportunity[] };
    pending:   { count: number; items: Opportunity[] };
  };
  total: number;
}

// ─── Revenue ──────────────────────────────────────────────────────────────────

export interface RevenueEntry {
  amount: number;
  type: 'revenue' | 'cost';
  source: string;
  description?: string;
  recorded_at: string;
}

export interface RevenueReport {
  total_revenue_usd: number;
  total_costs_usd: number;
  net_profit_usd: number;
  roi_pct: number;
  recent_revenue_30_entries: number;
  active_projects: number;
  generated_at: string;
}

export interface KPIs {
  total_revenue_usd: number;
  total_costs_usd: number;
  opportunities_discovered: number;
  ceo_kpis: {
    agents_active?: number;
    active_projects?: number;
    objectives_count?: number;
    timestamp?: string;
  };
}

// ─── Messages / Activity ──────────────────────────────────────────────────────

export interface AgentMessage {
  id: string;
  from: string;
  to: string;
  type: string;
  subject: string;
  content: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
  priority?: number;
}

export type ActivityType = 'info' | 'success' | 'warning' | 'error' | 'decision' | 'discovery';

export interface ActivityItem {
  id: string;
  agent: string;
  department: Department | string;
  message: string;
  type: ActivityType;
  timestamp: string;
  data?: Record<string, unknown>;
}

// ─── Memory ───────────────────────────────────────────────────────────────────

export interface Lesson {
  category: string;
  title: string;
  description: string;
  recommended_action: string;
  confidence: number;
  priority: number;
}

export interface KnowledgeInsight {
  insight: string;
  implication: string;
  priority: number;
}

// ─── System ───────────────────────────────────────────────────────────────────

export interface SystemConfig {
  opportunity_threshold: number;
  max_budget_usd: number;
  llm_provider: string;
  env: string;
}

export interface DashboardData {
  ceo: Record<string, unknown>;
  ceo_review: { review?: string; timestamp?: string } | null;
  finance: RevenueReport | null;
  approved_opportunities: number;
  pending_research: number;
  knowledge_insights: { insights?: KnowledgeInsight[] } | null;
  system_config: SystemConfig;
}

// ─── WebSocket Events ─────────────────────────────────────────────────────────

export interface WSMessage {
  type: 'init' | 'update' | 'ping' | 'activity';
  channel?: string;
  data?: Record<string, unknown>;
}

// ─── UI State ─────────────────────────────────────────────────────────────────

export type NavPage = 'dashboard' | 'agents' | 'opportunities' | 'revenue' | 'chat' | 'memory';
