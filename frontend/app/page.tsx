'use client';
import { motion } from 'framer-motion';
import { CEOPanel }             from '@/components/panels/CEOPanel';
import { ActivityFeed }         from '@/components/panels/ActivityFeed';
import { OrgChart }             from '@/components/panels/OrgChart';
import { OpportunityPipeline }  from '@/components/panels/OpportunityPipeline';
import { RevenueChart }         from '@/components/panels/RevenueChart';
import { AgentChat }            from '@/components/panels/AgentChat';
import { MemoryCenter }         from '@/components/panels/MemoryCenter';
import { useSystemStore }       from '@/store/useSystemStore';
import { MetricCard }           from '@/components/ui';
import { formatCurrency }       from '@/lib/utils';

const container = {
  hidden: {},
  show:   { transition: { staggerChildren: 0.06 } },
};
const item = {
  hidden: { opacity: 0, y: 16 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' } },
};

export default function DashboardPage() {
  const { kpis, revenue, pipelineApproved, pipelinePending, agents } = useSystemStore();
  const totalRev  = revenue?.total_revenue_usd ?? kpis?.total_revenue_usd ?? 0;
  const netProfit = revenue?.net_profit_usd ?? 0;
  const opps      = kpis?.opportunities_discovered ?? (pipelinePending.length + pipelineApproved.length);
  const active    = agents.filter(a => a.status === 'running').length;

  return (
    <motion.div variants={container} initial="hidden" animate="show" className="flex flex-col gap-3 h-full">

      {/* ── KPI strip ────────────────────────────────────────────── */}
      <motion.div variants={item} className="grid grid-cols-4 gap-3">
        <MetricCard label="Total Revenue"    value={formatCurrency(totalRev, true)}  icon="$"  color="#00ff94" subtext="All-time generated" />
        <MetricCard label="Net Profit"       value={formatCurrency(netProfit, true)} icon="↑"  color={netProfit >= 0 ? '#00ff94' : '#ef4444'} subtext="Revenue minus costs" />
        <MetricCard label="Opportunities"    value={String(opps)}                    icon="◈"  color="#9333ea" subtext="Discovered this cycle" />
        <MetricCard label="Active Agents"    value={`${active} / 22`}               icon="⬡"  color="#00c8ff" subtext={active > 0 ? 'System running' : 'System idle'} />
      </motion.div>

      {/* ── Row 2: CEO + Activity Feed ───────────────────────────── */}
      <div className="grid grid-cols-[320px_1fr] gap-3" style={{ minHeight: 320 }}>
        <motion.div variants={item} className="h-full">
          <CEOPanel />
        </motion.div>
        <motion.div variants={item} className="h-full">
          <ActivityFeed maxItems={60} />
        </motion.div>
      </div>

      {/* ── Row 3: Org Chart (full width) ────────────────────────── */}
      <motion.div variants={item} style={{ minHeight: 320 }}>
        <OrgChart />
      </motion.div>

      {/* ── Row 4: Pipeline + Revenue ──────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 380 }}>
        <motion.div variants={item} className="h-full">
          <OpportunityPipeline />
        </motion.div>
        <motion.div variants={item} className="h-full">
          <RevenueChart />
        </motion.div>
      </div>

      {/* ── Row 5: Chat + Memory ───────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3" style={{ minHeight: 380 }}>
        <motion.div variants={item} className="h-full">
          <AgentChat />
        </motion.div>
        <motion.div variants={item} className="h-full">
          <MemoryCenter />
        </motion.div>
      </div>

    </motion.div>
  );
}
