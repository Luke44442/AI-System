import React, { useState } from 'react';
import { useAppStore, ApprovalItem, Cycle } from '../store/appStore';

export default function RightPanel() {
  const { currentCycle, pastCycles, selectedCycleId } = useAppStore();

  const displayCycle: Cycle | null =
    selectedCycleId
      ? (pastCycles.find(c => c.id === selectedCycleId) ?? currentCycle)
      : currentCycle;

  if (!displayCycle) return <EmptyRight />;

  return (
    <div className="w-[340px] shrink-0 bg-surface border-l border-border flex flex-col overflow-hidden">
      <CycleHeader cycle={displayCycle} />
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {/* Hero opportunity */}
        {displayCycle.hero && <HeroCard opp={displayCycle.hero as any} />}

        {/* Blueprint summary */}
        {displayCycle.blueprint && <BlueprintCard bp={displayCycle.blueprint as any} />}

        {/* Approval queue */}
        {displayCycle.approvalItems?.length > 0 && (
          <ApprovalQueue cycle={displayCycle} />
        )}

        {/* Opportunities list */}
        {displayCycle.opportunities?.length > 0 && (
          <OpportunitiesList opps={displayCycle.opportunities as any[]} />
        )}
      </div>
    </div>
  );
}

function EmptyRight() {
  return (
    <div className="w-[340px] shrink-0 bg-surface border-l border-border flex flex-col items-center justify-center gap-3 text-center px-6">
      <div className="text-3xl opacity-30">📋</div>
      <div className="text-white/30 text-xs">Execution packages and store blueprints will appear here once a cycle completes.</div>
    </div>
  );
}

function CycleHeader({ cycle }: { cycle: Cycle }) {
  const pending = cycle.approvalItems?.filter(i => i.status === 'pending').length ?? 0;
  return (
    <div className="shrink-0 px-4 py-3 border-b border-border bg-surface-2/50">
      <div className="flex items-center justify-between">
        <div className="text-xs font-bold text-white">Execution Stack</div>
        {pending > 0 && (
          <div className="text-[9px] bg-agents-validation/20 text-agents-validation border border-agents-validation/30 rounded-full px-2 py-0.5 font-bold animate-pulse">
            {pending} PENDING
          </div>
        )}
      </div>
      <div className="text-[10px] text-white/30 mt-0.5">
        {cycle.mode.toUpperCase()} · {cycle.focusNiche ?? 'General'} · {new Date(cycle.startedAt).toLocaleDateString()}
      </div>
    </div>
  );
}

function HeroCard({ opp }: { opp: any }) {
  return (
    <div className="bg-surface-2 border border-agents-orchestrator/20 rounded-xl p-3">
      <div className="text-[9px] text-agents-orchestrator uppercase tracking-widest font-bold mb-2">Hero Opportunity</div>
      <div className="text-sm font-bold text-white">{opp.title}</div>
      <div className="text-[10px] text-white/50 mt-0.5">{opp.niche} · {opp.platform}</div>
      <div className="flex gap-2 mt-2">
        <Score label="Viral" value={opp.virality} color="text-agents-scout" />
        <Score label="Money" value={opp.monetization} color="text-agents-store" />
        <Score label="Score" value={opp.overall_score} color="text-agents-orchestrator" />
      </div>
      {opp.why_now && (
        <div className="text-[10px] text-white/40 mt-2 leading-relaxed">{opp.why_now}</div>
      )}
      {opp.price_range && (
        <div className="text-[10px] text-agents-store mt-1 font-bold">{opp.price_range}</div>
      )}
    </div>
  );
}

function BlueprintCard({ bp }: { bp: any }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-surface-2 border border-agents-store/20 rounded-xl p-3">
      <button
        className="w-full flex items-center justify-between"
        onClick={() => setOpen(v => !v)}
      >
        <div>
          <div className="text-[9px] text-agents-store uppercase tracking-widest font-bold">Store Blueprint</div>
          <div className="text-sm font-bold text-white text-left mt-0.5">{bp.store_name}</div>
        </div>
        <span className="text-white/30 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="mt-3 space-y-2 panel-slide-in">
          <div className="text-[10px] text-white/50 italic">"{bp.tagline}"</div>
          <div className="flex gap-1 mt-1">
            {bp.brand_colors && Object.values(bp.brand_colors).map((hex: any, i: number) => (
              <div key={i} className="w-5 h-5 rounded-full border border-white/10" style={{ background: hex }} />
            ))}
          </div>
          {bp.seo_keywords?.slice(0, 5).map((kw: string) => (
            <span key={kw} className="inline-block bg-surface border border-border rounded-md px-1.5 py-0.5 text-[9px] text-white/50 mr-1 mb-1">{kw}</span>
          ))}
          {bp.product_catalog?.length > 0 && (
            <div className="text-[9px] text-white/30 mt-1">{bp.product_catalog.length} products in catalog</div>
          )}
        </div>
      )}
    </div>
  );
}

function ApprovalQueue({ cycle }: { cycle: Cycle }) {
  return (
    <div>
      <div className="text-[9px] text-agents-validation uppercase tracking-widest font-bold mb-2 px-1">
        Approval Queue — NOTHING PUBLISHED YET
      </div>
      <div className="space-y-2">
        {cycle.approvalItems.map((item) => (
          <ApprovalCard key={item.id} item={item} cycleId={cycle.id} />
        ))}
      </div>
      <BulkActions cycle={cycle} />
    </div>
  );
}

function ApprovalCard({ item, cycleId }: { item: ApprovalItem; cycleId: string }) {
  const { updateApprovalItem } = useAppStore();
  const [expanded, setExpanded] = useState(false);

  async function handleAction(action: 'approved' | 'rejected') {
    await window.electronAPI.updateApproval({ cycleId, itemId: item.id, action });
    updateApprovalItem(cycleId, item.id, action);
  }

  const riskColor = item.risk === 'high' ? 'text-red-400' : item.risk === 'medium' ? 'text-agents-validation' : 'text-agents-store';

  return (
    <div className={`border rounded-xl overflow-hidden transition-all ${
      item.status === 'approved' ? 'border-agents-store/40 bg-agents-store/5' :
      item.status === 'rejected' ? 'border-red-500/20 bg-red-500/5 opacity-60' :
      'border-border bg-surface-2'
    }`}>
      <button className="w-full text-left p-3" onClick={() => setExpanded(v => !v)}>
        <div className="flex items-start justify-between gap-2">
          <div className="flex-1">
            <div className="flex items-center gap-1.5">
              <StatusIcon status={item.status} />
              <span className="text-xs font-bold text-white">{item.label}</span>
              <span className={`text-[8px] uppercase font-bold ${riskColor}`}>{item.risk} risk</span>
            </div>
            <div className="text-[10px] text-white/50 mt-0.5">{item.platform} · {item.estimated_time}</div>
          </div>
          <span className="text-white/20 text-xs shrink-0">{expanded ? '▲' : '▼'}</span>
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 panel-slide-in">
          <p className="text-[10px] text-white/60 leading-relaxed mb-3">{item.description}</p>
          {item.status === 'pending' && (
            <div className="flex gap-2">
              <button
                className="flex-1 h-7 rounded-lg bg-agents-store/20 border border-agents-store/40 text-agents-store text-[10px] font-bold hover:bg-agents-store/30 transition-colors"
                onClick={() => handleAction('approved')}
              >
                ✓ APPROVE
              </button>
              <button
                className="flex-1 h-7 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-[10px] font-bold hover:bg-red-500/20 transition-colors"
                onClick={() => handleAction('rejected')}
              >
                ✕ REJECT
              </button>
            </div>
          )}
          {item.status !== 'pending' && (
            <button
              className="text-[9px] text-white/30 hover:text-white/60 transition-colors"
              onClick={() => handleAction('pending' as any)}
            >
              Undo
            </button>
          )}
        </div>
      )}
    </div>
  );
}

function BulkActions({ cycle }: { cycle: Cycle }) {
  const { updateApprovalItem } = useAppStore();

  async function bulkApprove() {
    for (const item of cycle.approvalItems.filter(i => i.status === 'pending')) {
      await window.electronAPI.updateApproval({ cycleId: cycle.id, itemId: item.id, action: 'approved' });
      updateApprovalItem(cycle.id, item.id, 'approved');
    }
  }

  const pendingCount = cycle.approvalItems.filter(i => i.status === 'pending').length;
  if (pendingCount === 0) return null;

  return (
    <button
      className="w-full mt-2 h-8 rounded-xl border border-agents-store/30 text-agents-store text-[10px] font-bold hover:bg-agents-store/10 transition-colors"
      onClick={bulkApprove}
    >
      ✓ APPROVE ALL {pendingCount} ITEMS
    </button>
  );
}

function OpportunitiesList({ opps }: { opps: any[] }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="bg-surface-2 border border-border rounded-xl p-3">
      <button className="w-full flex items-center justify-between" onClick={() => setOpen(v => !v)}>
        <div className="text-[9px] text-agents-scout uppercase tracking-widest font-bold">
          {opps.length} Opportunities Found
        </div>
        <span className="text-white/30 text-xs">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="mt-2 space-y-1.5 panel-slide-in">
          {opps.slice(0, 10).map((o: any) => (
            <div key={o.id} className="flex items-center justify-between text-[10px]">
              <div className="flex-1 truncate text-white/70">{o.title}</div>
              <div className="flex gap-1 ml-2 shrink-0">
                <Score label="" value={o.overall_score} color="text-agents-scout" />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Score({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-0.5">
      {label && <span className="text-[9px] text-white/30">{label}</span>}
      <span className={`text-[10px] font-bold ${color}`}>{value}</span>
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === 'approved') return <span className="text-agents-store text-xs">✓</span>;
  if (status === 'rejected') return <span className="text-red-400 text-xs">✕</span>;
  return <span className="text-agents-validation text-xs">○</span>;
}
