'use client';
import { create } from 'zustand';
import type {
  Agent, Opportunity, RevenueReport, KPIs,
  AgentMessage, ActivityItem, Lesson, KnowledgeInsight,
  SystemConfig,
} from '@/types';

interface ChartPoint { time: string; revenue: number; costs: number; profit: number; }

interface SystemState {
  // Connection
  wsConnected: boolean;
  apiOnline: boolean;
  cycleRunning: boolean;

  // Agents
  agents: Agent[];
  deptSummary: Record<string, { running: number; idle: number; error: number; total: number }>;

  // Opportunities
  pipelinePending: Opportunity[];
  pipelineQualified: Opportunity[];
  pipelineApproved: Opportunity[];

  // Revenue
  revenue: RevenueReport | null;
  kpis: KPIs | null;
  revenueHistory: ChartPoint[];

  // Messages
  agentMessages: AgentMessage[];
  activityFeed: ActivityItem[];

  // Memory
  lessons: Lesson[];
  insights: KnowledgeInsight[];

  // CEO
  objectives: string[];
  ceoReview: string;
  activeProjects: number;

  // Config
  config: SystemConfig | null;

  // Actions
  setWsConnected:   (v: boolean) => void;
  setApiOnline:     (v: boolean) => void;
  setCycleRunning:  (v: boolean) => void;
  setAgents:        (agents: Agent[]) => void;
  setDeptSummary:   (s: Record<string, { running: number; idle: number; error: number; total: number }>) => void;
  setPipeline:      (pending: Opportunity[], qualified: Opportunity[], approved: Opportunity[]) => void;
  setRevenue:       (r: RevenueReport) => void;
  setKpis:          (k: KPIs) => void;
  pushRevenuePoint: (p: ChartPoint) => void;
  addMessage:       (m: AgentMessage) => void;
  addActivity:      (a: ActivityItem) => void;
  setLessons:       (l: Lesson[]) => void;
  setInsights:      (i: KnowledgeInsight[]) => void;
  setObjectives:    (o: string[]) => void;
  setCeoReview:     (r: string) => void;
  setActiveProjects:(n: number) => void;
  setConfig:        (c: SystemConfig) => void;
  applyDashboard:   (d: Record<string, unknown>) => void;
}

export const useSystemStore = create<SystemState>((set, get) => ({
  wsConnected:   false,
  apiOnline:     false,
  cycleRunning:  false,
  agents:        [],
  deptSummary:   {},
  pipelinePending:   [],
  pipelineQualified: [],
  pipelineApproved:  [],
  revenue:       null,
  kpis:          null,
  revenueHistory: [],
  agentMessages: [],
  activityFeed:  [],
  lessons:       [],
  insights:      [],
  objectives:    [
    'Identify 3+ high-score online income opportunities per week',
    'Maintain research pipeline with 20+ opportunities at scoring stage',
    'Achieve positive ROI on first execution within 90 days',
    'Continuously improve agent performance and prompt quality',
  ],
  ceoReview:     '',
  activeProjects: 0,
  config:        null,

  setWsConnected:  v => set({ wsConnected: v }),
  setApiOnline:    v => set({ apiOnline: v }),
  setCycleRunning: v => set({ cycleRunning: v }),
  setAgents:       agents => set({ agents }),
  setDeptSummary:  s => set({ deptSummary: s }),

  setPipeline: (pending, qualified, approved) =>
    set({ pipelinePending: pending, pipelineQualified: qualified, pipelineApproved: approved }),

  setRevenue: r => {
    set({ revenue: r });
    const hist = get().revenueHistory;
    const point: ChartPoint = {
      time:    new Date().toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' }),
      revenue: r.total_revenue_usd,
      costs:   r.total_costs_usd,
      profit:  r.net_profit_usd,
    };
    set({ revenueHistory: [...hist.slice(-19), point] });
  },

  setKpis: k => set({ kpis: k }),

  pushRevenuePoint: p => set(s => ({
    revenueHistory: [...s.revenueHistory.slice(-19), p],
  })),

  addMessage: m => set(s => ({
    agentMessages: [m, ...s.agentMessages].slice(0, 200),
  })),

  addActivity: a => set(s => ({
    activityFeed: [a, ...s.activityFeed].slice(0, 500),
  })),

  setLessons:  l => set({ lessons: l }),
  setInsights: i => set({ insights: i }),
  setObjectives:    o => set({ objectives: o }),
  setCeoReview:     r => set({ ceoReview: r }),
  setActiveProjects: n => set({ activeProjects: n }),
  setConfig:        c => set({ config: c }),

  applyDashboard: (d: Record<string, unknown>) => {
    const ceo = d.ceo as Record<string, unknown> | undefined;
    if (ceo?.objectives) get().setObjectives(ceo.objectives as string[]);
    if (ceo?.active_projects) get().setActiveProjects(ceo.active_projects as number);
    const rev = d.ceo_review as { review?: string } | null;
    if (rev?.review) get().setCeoReview(rev.review);
    const finance = d.finance as RevenueReport | null;
    if (finance) get().setRevenue(finance);
    if (d.approved_opportunities) get().setActiveProjects(d.approved_opportunities as number);
    if (d.system_config) get().setConfig(d.system_config as SystemConfig);
    const ki = d.knowledge_insights as { insights?: KnowledgeInsight[] } | null;
    if (ki?.insights) get().setInsights(ki.insights);
  },
}));
