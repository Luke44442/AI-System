import React, { useEffect, useRef } from 'react';
import { useAppStore, AgentId } from '../store/appStore';

const AGENT_META: Record<AgentId, { label: string; color: string; icon: string; glow: string }> = {
  orchestrator: { label: 'Orchestrator',  color: 'text-agents-orchestrator', icon: '🧠', glow: 'glow-orchestrator' },
  scout:        { label: 'Market Scout',  color: 'text-agents-scout',        icon: '🔎', glow: 'glow-scout' },
  validation:   { label: 'Validation',    color: 'text-agents-validation',   icon: '🧪', glow: 'glow-validation' },
  store:        { label: 'Store Builder', color: 'text-agents-store',        icon: '🏗️', glow: 'glow-store' },
  listing:      { label: 'Listing Engine',color: 'text-agents-listing',      icon: '🧾', glow: 'glow-listing' },
  product:      { label: 'Product Creator',color: 'text-agents-product',     icon: '🎨', glow: 'glow-product' },
  growth:       { label: 'Growth Engine', color: 'text-agents-growth',       icon: '📈', glow: 'glow-growth' },
};

const PIPELINE: AgentId[] = ['orchestrator', 'scout', 'validation', 'store', 'listing', 'product', 'growth'];

export default function CenterPanel() {
  const { centerBuffer, activeAgent, agentStatuses, cycleRunning, currentCycle } = useAppStore();
  const outputRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [centerBuffer]);

  const meta = activeAgent ? AGENT_META[activeAgent] : null;

  return (
    <div className="flex-1 flex flex-col bg-bg overflow-hidden">
      {/* Agent header */}
      <div className={`shrink-0 border-b border-border px-6 py-3 flex items-center gap-3 transition-all ${
        meta ? `bg-surface` : 'bg-bg'
      }`}>
        {meta ? (
          <>
            <div className={`text-2xl`}>{meta.icon}</div>
            <div>
              <div className={`font-bold text-sm ${meta.color}`}>{meta.label}</div>
              <div className="text-[10px] text-white/30 uppercase tracking-widest">
                {agentStatuses[activeAgent!] ?? 'active'}
              </div>
            </div>
            <div className="ml-auto flex items-center gap-1.5">
              {cycleRunning && (
                <div className="flex gap-0.5 items-center">
                  {[0, 1, 2].map(i => (
                    <div
                      key={i}
                      className={`w-1 h-3 rounded-full ${meta.color.replace('text-', 'bg-')} opacity-80`}
                      style={{ animationDelay: `${i * 0.15}s`, animation: 'barBounce 0.8s ease-in-out infinite' }}
                    />
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          <div className="text-white/20 text-sm">
            {cycleRunning ? 'Initializing...' : 'Waiting for cycle to start'}
          </div>
        )}
      </div>

      {/* Pipeline progress */}
      <div className="shrink-0 px-6 py-2 border-b border-border bg-surface/50">
        <div className="flex items-center gap-1">
          {PIPELINE.map((id, idx) => {
            const m = AGENT_META[id];
            const status = agentStatuses[id] ?? 'idle';
            const isActive = activeAgent === id;
            const isDone = status === 'complete';
            return (
              <React.Fragment key={id}>
                <div className={`flex items-center gap-1 px-2 py-1 rounded-lg text-[9px] font-bold transition-all ${
                  isActive ? `bg-surface-2 border border-current/30 ${m.color}` :
                  isDone   ? `${m.color} opacity-60` :
                  'text-white/20'
                }`}>
                  <span>{m.icon}</span>
                  <span className="hidden xl:inline">{m.label.split(' ')[0]}</span>
                </div>
                {idx < PIPELINE.length - 1 && (
                  <div className={`flex-1 h-px max-w-6 ${isDone ? 'bg-white/20' : 'bg-white/8'}`} />
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      {/* Output stream */}
      <div ref={outputRef} className="flex-1 overflow-y-auto px-6 py-4">
        {centerBuffer ? (
          <pre className={`agent-output ${cycleRunning ? 'cursor' : ''}`}>
            {centerBuffer}
          </pre>
        ) : (
          <IdleState cycleRunning={cycleRunning} done={currentCycle?.status === 'complete'} />
        )}
      </div>
    </div>
  );
}

function IdleState({ cycleRunning, done }: { cycleRunning: boolean; done: boolean }) {
  if (cycleRunning) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
        <div className="text-4xl animate-pulse">🧠</div>
        <div className="text-white/40 text-sm">Initializing agent swarm...</div>
      </div>
    );
  }
  if (done) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-center">
        <div className="text-4xl">✅</div>
        <div className="text-agents-store text-sm font-bold">Cycle Complete</div>
        <div className="text-white/40 text-xs">Review approval items in the right panel</div>
      </div>
    );
  }
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
      <div className="text-5xl mb-2">⚡</div>
      <div className="text-white font-bold text-lg">ANDROOAGI</div>
      <div className="text-white/40 text-sm leading-relaxed max-w-xs">
        Your personal AI business engine. Press <span className="text-agents-orchestrator font-bold">START CYCLE</span> to begin discovering profitable opportunities.
      </div>
      <div className="grid grid-cols-3 gap-3 mt-4 w-full max-w-sm text-xs text-white/30">
        <div className="bg-surface-2 border border-border rounded-xl p-3">
          <div className="text-lg mb-1">🔎</div>Scans markets
        </div>
        <div className="bg-surface-2 border border-border rounded-xl p-3">
          <div className="text-lg mb-1">🏗️</div>Builds stores
        </div>
        <div className="bg-surface-2 border border-border rounded-xl p-3">
          <div className="text-lg mb-1">📈</div>Plans launch
        </div>
      </div>
    </div>
  );
}
