import { create } from 'zustand';

export type AgentId = 'orchestrator' | 'scout' | 'validation' | 'store' | 'listing' | 'product' | 'growth';
export type AgentStatus = 'idle' | 'thinking' | 'active' | 'parsing' | 'packaging' | 'complete' | 'error';
export type CycleMode = 'explore' | 'build' | 'launch';

export interface AgentEvent {
  id: string;
  agent: AgentId;
  label: string;
  timestamp: number;
  type: 'status' | 'chunk' | 'complete' | 'error';
  message?: string;
  text?: string;
  status?: AgentStatus;
  summary?: string;
}

export interface ApprovalItem {
  id: string;
  type: string;
  label: string;
  description: string;
  details: Record<string, unknown>;
  status: 'pending' | 'approved' | 'rejected';
  risk: 'low' | 'medium' | 'high';
  platform: string;
  estimated_time: string;
}

export interface Cycle {
  id: string;
  mode: CycleMode;
  focusNiche?: string | null;
  startedAt: string;
  completedAt?: string;
  status: 'running' | 'complete' | 'error' | 'stopped';
  opportunities: unknown[];
  validated: unknown[] | null;
  hero: unknown | null;
  blueprint: unknown | null;
  listings: unknown[];
  productSpec: unknown | null;
  growthPlan: unknown | null;
  executionPackage: unknown | null;
  approvalItems: ApprovalItem[];
  approvalStatus: 'none' | 'pending' | 'partial' | 'all_approved' | 'all_rejected';
}

export interface AppState {
  // Runtime
  cycleRunning: boolean;
  activeAgent: AgentId | null;
  agentStatuses: Partial<Record<AgentId, AgentStatus>>;
  feedEvents: AgentEvent[];
  centerBuffer: string;

  // Data
  currentCycle: Cycle | null;
  pastCycles: Cycle[];
  stats: { totalOppsFound: number; totalCycles: number; readyToLaunch: number };

  // UI
  selectedCycleId: string | null;
  settingsOpen: boolean;
  activeTab: 'feed' | 'cycle';

  // Actions
  setCycleRunning: (v: boolean) => void;
  setActiveAgent: (agent: AgentId | null) => void;
  pushFeedEvent: (evt: AgentEvent) => void;
  appendCenterBuffer: (text: string) => void;
  clearCenterBuffer: () => void;
  setCurrentCycle: (cycle: Cycle | null) => void;
  setPastCycles: (cycles: Cycle[]) => void;
  setStats: (s: AppState['stats']) => void;
  setSelectedCycle: (id: string | null) => void;
  setSettingsOpen: (v: boolean) => void;
  setActiveTab: (tab: 'feed' | 'cycle') => void;
  updateApprovalItem: (cycleId: string, itemId: string, status: 'approved' | 'rejected') => void;
  setAgentStatus: (agent: AgentId, status: AgentStatus) => void;
}

export const useAppStore = create<AppState>((set) => ({
  cycleRunning: false,
  activeAgent: null,
  agentStatuses: {},
  feedEvents: [],
  centerBuffer: '',

  currentCycle: null,
  pastCycles: [],
  stats: { totalOppsFound: 0, totalCycles: 0, readyToLaunch: 0 },

  selectedCycleId: null,
  settingsOpen: false,
  activeTab: 'feed',

  setCycleRunning: (v) => set({ cycleRunning: v }),
  setActiveAgent: (agent) => set({ activeAgent: agent }),
  setAgentStatus: (agent, status) =>
    set((s) => ({ agentStatuses: { ...s.agentStatuses, [agent]: status } })),

  pushFeedEvent: (evt) =>
    set((s) => ({
      feedEvents: [evt, ...s.feedEvents].slice(0, 200),
    })),

  appendCenterBuffer: (text) =>
    set((s) => ({ centerBuffer: s.centerBuffer + text })),

  clearCenterBuffer: () => set({ centerBuffer: '' }),

  setCurrentCycle: (cycle) => set({ currentCycle: cycle }),
  setPastCycles: (cycles) => set({ pastCycles: cycles }),
  setStats: (stats) => set({ stats }),
  setSelectedCycle: (id) => set({ selectedCycleId: id }),
  setSettingsOpen: (v) => set({ settingsOpen: v }),
  setActiveTab: (tab) => set({ activeTab: tab }),

  updateApprovalItem: (cycleId, itemId, status) =>
    set((s) => {
      const updateItems = (items: ApprovalItem[]) =>
        items.map((i) => (i.id === itemId ? { ...i, status } : i));

      return {
        currentCycle:
          s.currentCycle?.id === cycleId
            ? { ...s.currentCycle, approvalItems: updateItems(s.currentCycle.approvalItems) }
            : s.currentCycle,
        pastCycles: s.pastCycles.map((c) =>
          c.id === cycleId ? { ...c, approvalItems: updateItems(c.approvalItems) } : c
        ),
      };
    }),
}));
