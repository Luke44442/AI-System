import React, { useEffect, useRef } from 'react';
import { useAppStore, AgentId, AgentEvent } from './store/appStore';
import TopBar from './components/TopBar';
import LeftPanel from './components/LeftPanel';
import CenterPanel from './components/CenterPanel';
import RightPanel from './components/RightPanel';
import SettingsModal from './components/SettingsModal';

let eventSeq = 0;
function nextId() { return `evt-${++eventSeq}`; }

export default function App() {
  const {
    setCycleRunning,
    setActiveAgent,
    setAgentStatus,
    pushFeedEvent,
    appendCenterBuffer,
    clearCenterBuffer,
    setCurrentCycle,
    setPastCycles,
    setStats,
  } = useAppStore();

  const unsubscribers = useRef<Array<() => void>>([]);

  useEffect(() => {
    // Load initial data
    async function init() {
      const [cycles, stats] = await Promise.all([
        window.electronAPI.listCycles(),
        window.electronAPI.getStats(),
      ]);
      setPastCycles(cycles);
      setStats(stats);
      if (cycles[0]?.status === 'complete') {
        setCurrentCycle(cycles[0]);
      }
    }
    init();

    // Subscribe to IPC events
    const unsubs = [
      window.electronAPI.on('cycle:started', (data: any) => {
        setCycleRunning(true);
        clearCenterBuffer();
        setCurrentCycle(null);
        setActiveAgent('orchestrator');
        pushFeedEvent({
          id: nextId(),
          agent: 'orchestrator',
          label: 'Orchestrator',
          timestamp: Date.now(),
          type: 'status',
          status: 'active',
          message: `Cycle started — mode: ${data.mode}${data.focusNiche ? ` / ${data.focusNiche}` : ''}`,
        });
      }),

      window.electronAPI.on('agent:status', (data: any) => {
        const agent = data.agent as AgentId;
        setActiveAgent(agent);
        setAgentStatus(agent, data.status);
        pushFeedEvent({
          id: nextId(),
          agent,
          label: data.label ?? agent,
          timestamp: Date.now(),
          type: 'status',
          status: data.status,
          message: data.message,
        });
      }),

      window.electronAPI.on('agent:chunk', (data: any) => {
        appendCenterBuffer(data.text ?? '');
      }),

      window.electronAPI.on('agent:complete', (data: any) => {
        const agent = data.agent as AgentId;
        setAgentStatus(agent, 'complete');
        pushFeedEvent({
          id: nextId(),
          agent,
          label: data.label ?? agent,
          timestamp: Date.now(),
          type: 'complete',
          summary: data.summary,
        });
      }),

      window.electronAPI.on('cycle:complete', async (cycle: any) => {
        setCycleRunning(false);
        setActiveAgent(null);
        setCurrentCycle(cycle);

        // Refresh full list and stats
        const [cycles, stats] = await Promise.all([
          window.electronAPI.listCycles(),
          window.electronAPI.getStats(),
        ]);
        setPastCycles(cycles);
        setStats(stats);

        pushFeedEvent({
          id: nextId(),
          agent: 'orchestrator',
          label: 'Orchestrator',
          timestamp: Date.now(),
          type: 'complete',
          summary: `✅ Cycle complete — ${cycle.opportunities?.length ?? 0} opps, ${cycle.approvalItems?.length ?? 0} items ready`,
        });
      }),

      window.electronAPI.on('cycle:stopped', () => {
        setCycleRunning(false);
        setActiveAgent(null);
        pushFeedEvent({
          id: nextId(),
          agent: 'orchestrator',
          label: 'Orchestrator',
          timestamp: Date.now(),
          type: 'status',
          message: 'Cycle stopped by user',
        });
      }),

      window.electronAPI.on('cycle:error', (data: any) => {
        setCycleRunning(false);
        setActiveAgent(null);
        pushFeedEvent({
          id: nextId(),
          agent: 'orchestrator',
          label: 'Orchestrator',
          timestamp: Date.now(),
          type: 'error',
          message: `Error: ${data.message}`,
        });
      }),
    ].filter(Boolean) as Array<() => void>;

    unsubscribers.current = unsubs;
    return () => { unsubs.forEach(fn => fn()); };
  }, []);

  return (
    <div className="flex flex-col h-screen w-screen overflow-hidden">
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <LeftPanel />
        <CenterPanel />
        <RightPanel />
      </div>
      <SettingsModal />
    </div>
  );
}
