import React, { useEffect, useRef } from 'react';
import { useAppStore, AgentEvent, AgentId } from '../store/appStore';

const AGENT_META: Record<AgentId, { label: string; color: string; icon: string }> = {
  orchestrator: { label: 'Orchestrator', color: 'text-agents-orchestrator', icon: '🧠' },
  scout:        { label: 'Market Scout', color: 'text-agents-scout',        icon: '🔎' },
  validation:   { label: 'Validation',   color: 'text-agents-validation',   icon: '🧪' },
  store:        { label: 'Store Builder',color: 'text-agents-store',        icon: '🏗️' },
  listing:      { label: 'Listing Engine',color: 'text-agents-listing',    icon: '🧾' },
  product:      { label: 'Product Creator',color: 'text-agents-product',   icon: '🎨' },
  growth:       { label: 'Growth Engine',color: 'text-agents-growth',       icon: '📈' },
};

export default function LeftPanel() {
  const { feedEvents, agentStatuses, activeAgent, pastCycles, setSelectedCycle, activeTab, setActiveTab } = useAppStore();
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (feedRef.current && activeTab === 'feed') {
      feedRef.current.scrollTop = 0;
    }
  }, [feedEvents.length, activeTab]);

  return (
    <div className="flex flex-col w-[300px] shrink-0 bg-surface border-r border-border overflow-hidden">
      {/* Agent status grid */}
      <div className="p-3 border-b border-border">
        <div className="text-[10px] text-white/30 uppercase tracking-widest mb-2">Agent Swarm</div>
        <div className="grid grid-cols-2 gap-1.5">
          {(Object.keys(AGENT_META) as AgentId[]).map((id) => {
            const meta = AGENT_META[id];
            const status = agentStatuses[id] ?? 'idle';
            const isActive = activeAgent === id;
            return (
              <div
                key={id}
                className={`rounded-lg px-2 py-1.5 border transition-all ${
                  isActive
                    ? 'bg-surface-2 border-current/30 ' + meta.color
                    : 'bg-surface-2/50 border-border'
                }`}
              >
                <div className="flex items-center gap-1">
                  <span className="text-xs">{meta.icon}</span>
                  <span className={`text-[10px] font-bold truncate ${isActive ? meta.color : 'text-white/50'}`}>
                    {meta.label}
                  </span>
                </div>
                <StatusDot status={status} />
              </div>
            );
          })}
        </div>
      </div>

      {/* Tab switcher */}
      <div className="flex border-b border-border shrink-0">
        {(['feed', 'cycle'] as const).map((tab) => (
          <button
            key={tab}
            className={`flex-1 py-2 text-[10px] uppercase tracking-widest font-bold transition-colors ${
              activeTab === tab ? 'text-white border-b-2 border-agents-orchestrator' : 'text-white/30 hover:text-white/60'
            }`}
            onClick={() => setActiveTab(tab)}
          >
            {tab === 'feed' ? 'Live Feed' : 'History'}
          </button>
        ))}
      </div>

      {/* Content */}
      {activeTab === 'feed' ? (
        <div ref={feedRef} className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {feedEvents.length === 0 && (
            <div className="text-center text-white/20 text-xs mt-8 px-4">
              Start a cycle to see live agent activity
            </div>
          )}
          {feedEvents.map((evt) => (
            <FeedCard key={evt.id} evt={evt} />
          ))}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto p-2 space-y-1.5">
          {pastCycles.length === 0 && (
            <div className="text-center text-white/20 text-xs mt-8">No cycles yet</div>
          )}
          {pastCycles.map((c) => (
            <button
              key={c.id}
              className="w-full text-left bg-surface-2 hover:bg-surface-2/80 border border-border rounded-xl p-3 transition-colors panel-slide-in"
              onClick={() => setSelectedCycle(c.id)}
            >
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-bold text-white/60 uppercase">{c.mode}</span>
                <span className={`text-[9px] px-1.5 py-0.5 rounded-full ${
                  c.approvalStatus === 'pending' ? 'bg-agents-validation/20 text-agents-validation' :
                  c.approvalStatus === 'all_approved' ? 'bg-agents-store/20 text-agents-store' :
                  'bg-white/10 text-white/40'
                }`}>
                  {c.approvalStatus === 'pending' ? 'NEEDS REVIEW' :
                   c.approvalStatus === 'all_approved' ? 'APPROVED' : c.status.toUpperCase()}
                </span>
              </div>
              <div className="text-xs text-white mt-1 truncate">
                {(c.hero as any)?.title ?? c.focusNiche ?? 'General scan'}
              </div>
              <div className="text-[9px] text-white/30 mt-0.5">
                {new Date(c.startedAt).toLocaleDateString()} · {c.opportunities?.length ?? 0} opps
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

function FeedCard({ evt }: { evt: AgentEvent }) {
  const meta = AGENT_META[evt.agent] ?? { label: evt.agent, color: 'text-white/60', icon: '·' };

  if (evt.type === 'chunk') return null; // chunks only go to center

  return (
    <div className="bg-surface-2/60 border border-border rounded-xl p-2.5 panel-slide-in">
      <div className="flex items-center gap-1.5 mb-1">
        <span className="text-xs">{meta.icon}</span>
        <span className={`text-[10px] font-bold ${meta.color}`}>{meta.label}</span>
        <span className="text-[9px] text-white/25 ml-auto">
          {new Date(evt.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
        </span>
      </div>
      <p className="text-[11px] text-white/70 leading-relaxed">
        {evt.summary ?? evt.message}
      </p>
    </div>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors: Record<string, string> = {
    idle:      'bg-white/20',
    thinking:  'bg-agents-validation animate-pulse',
    active:    'bg-agents-scout animate-pulse',
    parsing:   'bg-agents-listing animate-pulse',
    packaging: 'bg-agents-product animate-pulse',
    complete:  'bg-agents-store',
    error:     'bg-red-500',
  };
  return (
    <div className="flex items-center gap-1 mt-0.5">
      <div className={`w-1.5 h-1.5 rounded-full ${colors[status] ?? 'bg-white/20'}`} />
      <span className="text-[9px] text-white/30">{status}</span>
    </div>
  );
}
