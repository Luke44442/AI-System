'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import { OpportunityPipeline } from '@/components/panels/OpportunityPipeline';
import { GlassCard, PanelHeader, ScoreRing, ScoreBar, NeonBadge } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { scoreGrade, formatCurrency } from '@/lib/utils';
import { Target, Filter } from 'lucide-react';
import type { Opportunity } from '@/types';

function FullOppCard({ opp }: { opp: Opportunity }) {
  const { grade, color } = scoreGrade(opp.overall_score);
  const title = opp.title ?? opp.name ?? 'Unknown';

  return (
    <motion.div
      layout
      initial={{ opacity: 0, scale: 0.96 }}
      animate={{ opacity: 1, scale: 1 }}
      className="p-4 rounded border border-[rgba(255,255,255,0.07)] bg-surface-mid/40 hover:border-[rgba(0,200,255,0.2)] transition-all"
    >
      <div className="flex items-start gap-3 mb-3">
        <ScoreRing score={Math.round(opp.overall_score)} size={52} stroke={4} color={color} grade={grade} />
        <div className="flex-1">
          <div className="font-mono text-sm font-bold text-slate-100">{title}</div>
          <div className="font-mono text-[9px] text-slate-500 mt-0.5">{opp.category}</div>
          <div className="flex items-center gap-2 mt-1.5 flex-wrap">
            <NeonBadge label={opp.status} color={opp.status === 'approved' ? '#00ff94' : '#00c8ff'} />
            {opp.estimated_monthly_revenue_usd && (
              <NeonBadge label={`${formatCurrency(opp.estimated_monthly_revenue_usd, true)}/mo`} color="#f59e0b" />
            )}
          </div>
        </div>
      </div>

      {opp.description && (
        <p className="font-mono text-[9px] text-slate-400 mb-3 leading-relaxed line-clamp-2">{opp.description}</p>
      )}

      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5">
        {[
          { key: 'profit_potential',    label: 'Profit Potential',    color: '#00ff94' },
          { key: 'automation_potential',label: 'Automation',           color: '#00c8ff' },
          { key: 'scalability',         label: 'Scalability',          color: '#9333ea' },
          { key: 'risk_level',          label: 'Safety',               color: '#f59e0b' },
          { key: 'difficulty',          label: 'Ease of Entry',        color: '#ec4899' },
          { key: 'time_required',       label: 'Speed to Revenue',     color: '#a78bfa' },
        ].map(({ key, label, color: c }) => (
          <ScoreBar
            key={key}
            score={(opp as unknown as Record<string, number>)[key] ?? 0}
            label={label}
            color={c}
          />
        ))}
      </div>
    </motion.div>
  );
}

export default function OpportunitiesPage() {
  const { pipelinePending, pipelineQualified, pipelineApproved } = useSystemStore();
  const [filter, setFilter] = useState<'all' | 'approved' | 'qualified' | 'pending'>('all');

  const allOpps = [...pipelineApproved, ...pipelineQualified, ...pipelinePending];
  const filtered = filter === 'all' ? allOpps
    : filter === 'approved'  ? pipelineApproved
    : filter === 'qualified' ? pipelineQualified
    : pipelinePending;

  const sorted = [...filtered].sort((a, b) => b.overall_score - a.overall_score);

  return (
    <div className="flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="font-orbitron text-base font-bold text-neon-blue">Opportunity Pipeline</div>
        <div className="flex items-center gap-2">
          <Filter size={12} className="text-slate-500" />
          {(['all', 'approved', 'qualified', 'pending'] as const).map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`font-mono text-[9px] px-3 py-1 rounded-sm transition-all capitalize ${
                filter === f
                  ? 'bg-neon-blue/15 text-neon-blue border border-neon-blue/25'
                  : 'text-slate-500 hover:text-slate-300 border border-transparent'
              }`}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Kanban pipeline */}
      <div style={{ minHeight: 380 }}>
        <OpportunityPipeline />
      </div>

      {/* Full list */}
      <GlassCard noPad>
        <PanelHeader
          title={`All Opportunities (${sorted.length})`}
          icon={<Target size={12} />}
          badge={`threshold: 65`}
          badgeColor="#9333ea"
        />
        <div className="p-3">
          {sorted.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
              {sorted.map((opp, i) => <FullOppCard key={(opp.title ?? opp.name ?? '') + i} opp={opp} />)}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-16 gap-3">
              <Target size={32} className="text-slate-700" />
              <span className="font-mono text-[11px] text-slate-500">No opportunities yet — run a research cycle</span>
            </div>
          )}
        </div>
      </GlassCard>
    </div>
  );
}
