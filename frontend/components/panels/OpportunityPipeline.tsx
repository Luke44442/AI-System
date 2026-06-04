'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { Target, ChevronRight } from 'lucide-react';
import { GlassCard, PanelHeader, ScoreRing, NeonBadge, ScoreBar } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { scoreGrade, formatCurrency } from '@/lib/utils';
import type { Opportunity } from '@/types';

const STAGE_CONFIG = [
  { key: 'pending',   label: 'Discovered', color: '#475569', items: [] as Opportunity[] },
  { key: 'qualified', label: 'Qualified',  color: '#9333ea', items: [] as Opportunity[] },
  { key: 'approved',  label: 'Approved',   color: '#00ff94', items: [] as Opportunity[] },
];

function OppCard({ opp, color }: { opp: Opportunity; color: string }) {
  const title = opp.title ?? opp.name ?? 'Unknown';
  const { grade } = scoreGrade(opp.overall_score);
  const rev = opp.estimated_monthly_revenue_usd;

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-2.5 rounded border border-[rgba(255,255,255,0.06)] bg-surface-mid/30 hover:border-[rgba(255,255,255,0.1)] transition-all group cursor-default"
    >
      <div className="flex items-start gap-2">
        <ScoreRing score={Math.round(opp.overall_score)} size={36} stroke={3} color={color} grade={grade} />
        <div className="flex-1 min-w-0">
          <div className="font-mono text-[10px] font-bold text-slate-200 truncate" title={title}>{title}</div>
          <div className="font-mono text-[8px] text-slate-500 mt-0.5">{opp.category ?? 'online'}</div>
          {rev && (
            <div className="font-mono text-[9px] mt-1" style={{ color }}>
              {formatCurrency(rev, true)}/mo
            </div>
          )}
        </div>
      </div>
      {/* Score bars */}
      <div className="mt-2 grid grid-cols-2 gap-x-3 gap-y-1">
        <ScoreBar score={opp.profit_potential}   label="Profit"     color="#00ff94" className="text-[7px]" />
        <ScoreBar score={opp.automation_potential} label="Auto"   color="#00c8ff" className="text-[7px]" />
        <ScoreBar score={opp.scalability}          label="Scale"   color="#9333ea" className="text-[7px]" />
        <ScoreBar score={opp.risk_level}            label="Safety"  color="#f59e0b" className="text-[7px]" />
      </div>
    </motion.div>
  );
}

export function OpportunityPipeline() {
  const { pipelinePending, pipelineQualified, pipelineApproved } = useSystemStore();
  const stages = [
    { ...STAGE_CONFIG[0], items: pipelinePending   },
    { ...STAGE_CONFIG[1], items: pipelineQualified },
    { ...STAGE_CONFIG[2], items: pipelineApproved  },
  ];
  const total = pipelinePending.length + pipelineQualified.length + pipelineApproved.length;

  return (
    <GlassCard noPad className="h-full flex flex-col">
      <PanelHeader
        title="Opportunity Pipeline"
        badge={`${total} total`}
        badgeColor="#9333ea"
        icon={<Target size={12} />}
      />

      {/* Stage headers */}
      <div className="grid grid-cols-3 border-b border-[rgba(255,255,255,0.04)]">
        {stages.map(stage => (
          <div key={stage.key} className="flex flex-col items-center py-2 border-r last:border-0 border-[rgba(255,255,255,0.04)]">
            <div className="font-orbitron text-[8px] tracking-wider" style={{ color: stage.color }}>
              {stage.label}
            </div>
            <div className="font-orbitron font-bold text-lg mt-0.5" style={{ color: stage.color, textShadow: `0 0 10px ${stage.color}40` }}>
              {stage.items.length}
            </div>
            {/* Progress bar */}
            <div className="w-12 h-0.5 mt-1 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ background: stage.color }}
                initial={{ width: 0 }}
                animate={{ width: `${total > 0 ? (stage.items.length / total) * 100 : 0}%` }}
                transition={{ duration: 0.8, ease: 'easeOut' }}
              />
            </div>
          </div>
        ))}
      </div>

      {/* Opportunity cards */}
      <div className="grid grid-cols-3 gap-0 flex-1 overflow-hidden">
        {stages.map(stage => (
          <div key={stage.key} className="overflow-y-auto p-2 space-y-2 border-r last:border-0 border-[rgba(255,255,255,0.04)]">
            <AnimatePresence>
              {stage.items.slice(0, 8).map((opp, i) => (
                <OppCard key={opp.title ?? i} opp={opp} color={stage.color} />
              ))}
            </AnimatePresence>
            {stage.items.length === 0 && (
              <div className="flex items-center justify-center h-20">
                <span className="font-mono text-[9px] text-slate-600">No items yet</span>
              </div>
            )}
          </div>
        ))}
      </div>
    </GlassCard>
  );
}
