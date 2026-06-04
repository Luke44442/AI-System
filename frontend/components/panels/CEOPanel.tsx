'use client';
import { motion, AnimatePresence } from 'framer-motion';
import { Crown, Target, TrendingUp, Zap, ChevronRight } from 'lucide-react';
import { GlassCard, PanelHeader, PulsingDot, CyberButton, MetricCard } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { formatCurrency } from '@/lib/utils';

export function CEOPanel() {
  const { objectives, ceoReview, revenue, activeProjects, cycleRunning, setCycleRunning } = useSystemStore();
  const profit = revenue?.net_profit_usd ?? 0;
  const roi    = revenue?.roi_pct ?? 0;

  return (
    <GlassCard noPad glow="blue" className="flex flex-col h-full">
      <PanelHeader
        title="Supreme Agent — CEO"
        badge="EXECUTIVE"
        badgeColor="#f59e0b"
        icon={<Crown size={12} />}
        right={
          <div className="flex items-center gap-1.5">
            <PulsingDot color="#f59e0b" size={6} />
            <span className="font-mono text-[8px] text-amber-400">ONLINE</span>
          </div>
        }
      />

      <div className="p-4 flex flex-col gap-4 flex-1">
        {/* Quick stats */}
        <div className="grid grid-cols-2 gap-2">
          <div className="p-2 rounded border border-[rgba(245,158,11,0.15)] bg-[rgba(245,158,11,0.05)]">
            <div className="font-mono text-[8px] text-amber-500/60 tracking-wider">NET PROFIT</div>
            <div className="font-orbitron font-bold text-base mt-0.5" style={{ color: profit >= 0 ? '#00ff94' : '#ef4444' }}>
              {formatCurrency(profit)}
            </div>
          </div>
          <div className="p-2 rounded border border-[rgba(0,200,255,0.1)] bg-[rgba(0,200,255,0.04)]">
            <div className="font-mono text-[8px] text-slate-500 tracking-wider">ACTIVE PROJECTS</div>
            <div className="font-orbitron font-bold text-base text-neon-blue mt-0.5">{activeProjects}</div>
          </div>
        </div>

        {/* Objectives */}
        <div>
          <div className="font-mono text-[8px] text-slate-500 tracking-[0.2em] uppercase mb-2 flex items-center gap-1.5">
            <Target size={9} />
            Active Objectives
          </div>
          <ul className="space-y-1.5">
            <AnimatePresence mode="popLayout">
              {objectives.slice(0, 4).map((obj, i) => (
                <motion.li
                  key={obj}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 8 }}
                  transition={{ delay: i * 0.05 }}
                  className="flex items-start gap-2 text-[10px] font-mono text-slate-300 leading-relaxed pl-2 border-l border-amber-500/30"
                >
                  <ChevronRight size={9} className="text-amber-400 mt-0.5 flex-shrink-0" />
                  {obj}
                </motion.li>
              ))}
            </AnimatePresence>
          </ul>
        </div>

        {/* Latest review */}
        {ceoReview && (
          <div>
            <div className="font-mono text-[8px] text-slate-500 tracking-[0.2em] uppercase mb-2">Latest Review</div>
            <div className="relative p-3 rounded border border-amber-500/10 bg-amber-500/5">
              <div className="font-mono text-[9px] text-slate-300 leading-relaxed max-h-[72px] overflow-hidden text-ellipsis">
                {ceoReview.slice(0, 220)}{ceoReview.length > 220 ? '...' : ''}
              </div>
            </div>
          </div>
        )}

        {/* Strategy status */}
        <div className="mt-auto">
          <div className="flex items-center gap-2 p-2.5 rounded border border-[rgba(0,255,148,0.1)] bg-[rgba(0,255,148,0.04)]">
            <Zap size={11} className="text-neon-green flex-shrink-0" />
            <div>
              <div className="font-mono text-[8px] text-neon-green tracking-wider">SYSTEM STATUS</div>
              <div className="font-mono text-[9px] text-slate-300">
                {cycleRunning ? 'Running research cycle...' : 'Autonomous mode — awaiting next cycle'}
              </div>
            </div>
          </div>
        </div>
      </div>
    </GlassCard>
  );
}
