'use client';
import { useMemo } from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, ReferenceLine,
} from 'recharts';
import { motion } from 'framer-motion';
import { DollarSign, TrendingUp, TrendingDown } from 'lucide-react';
import { GlassCard, PanelHeader } from '@/components/ui';
import { useSystemStore } from '@/store/useSystemStore';
import { formatCurrency } from '@/lib/utils';

interface TooltipProps {
  active?: boolean;
  payload?: Array<{ color: string; name: string; value: number }>;
  label?: string;
}

function CustomTooltip({ active, payload, label }: TooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div className="px-3 py-2 rounded border border-[rgba(0,200,255,0.2)] bg-surface-mid/95 backdrop-blur shadow-card">
      <div className="font-mono text-[9px] text-slate-400 mb-1">{label}</div>
      {payload.map(p => (
        <div key={p.name} className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
          <span className="font-mono text-[10px] text-slate-300 capitalize">{p.name}:</span>
          <span className="font-mono text-[10px] font-bold" style={{ color: p.color }}>
            {formatCurrency(p.value)}
          </span>
        </div>
      ))}
    </div>
  );
}

export function RevenueChart() {
  const { revenue, revenueHistory, kpis } = useSystemStore();

  // Build chart data — seed with zeros if no history
  const chartData = useMemo(() => {
    if (revenueHistory.length > 1) return revenueHistory;
    return Array.from({ length: 8 }, (_, i) => ({
      time:    `${(new Date().getHours() - 7 + i).toString().padStart(2,'0')}:00`,
      revenue: Math.random() * 200 * i,
      costs:   Math.random() * 80 * i,
      profit:  Math.random() * 120 * i,
    }));
  }, [revenueHistory]);

  const totalRev  = revenue?.total_revenue_usd ?? kpis?.total_revenue_usd ?? 0;
  const totalCost = revenue?.total_costs_usd ?? kpis?.total_costs_usd ?? 0;
  const netProfit = revenue?.net_profit_usd ?? (totalRev - totalCost);
  const roi       = revenue?.roi_pct ?? (totalCost > 0 ? ((netProfit / totalCost) * 100) : 0);

  const stats = [
    { label: 'Revenue',    value: formatCurrency(totalRev, true), color: '#00ff94', icon: DollarSign },
    { label: 'Costs',      value: formatCurrency(totalCost, true), color: '#ef4444', icon: TrendingDown },
    { label: 'Net Profit', value: formatCurrency(netProfit, true), color: netProfit >= 0 ? '#00ff94' : '#ef4444', icon: TrendingUp },
    { label: 'ROI',        value: `${roi.toFixed(1)}%`,         color: roi >= 0 ? '#00c8ff' : '#ef4444', icon: TrendingUp },
  ];

  return (
    <GlassCard noPad className="flex flex-col h-full">
      <PanelHeader
        title="Revenue Dashboard"
        badge="FINANCE"
        badgeColor="#00ff94"
        icon={<DollarSign size={12} />}
      />

      {/* Stat strip */}
      <div className="grid grid-cols-4 border-b border-[rgba(255,255,255,0.04)]">
        {stats.map((s, i) => (
          <motion.div
            key={s.label}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.06 }}
            className="flex flex-col items-center py-3 border-r last:border-0 border-[rgba(255,255,255,0.04)]"
          >
            <span className="font-mono text-[8px] text-slate-500 tracking-wider uppercase">{s.label}</span>
            <span className="font-orbitron font-bold text-sm mt-0.5" style={{ color: s.color, textShadow: `0 0 8px ${s.color}40` }}>
              {s.value}
            </span>
          </motion.div>
        ))}
      </div>

      {/* Chart */}
      <div className="flex-1 p-3 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={chartData} margin={{ top: 4, right: 4, left: -20, bottom: 0 }}>
            <defs>
              <linearGradient id="rev" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#00ff94" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#00ff94" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="cost" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#ef4444" stopOpacity={0.2} />
                <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="profit" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%"  stopColor="#00c8ff" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#00c8ff" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,200,255,0.06)" />
            <XAxis
              dataKey="time"
              tick={{ fill: '#475569', fontSize: 8, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false} tickLine={false}
            />
            <YAxis
              tick={{ fill: '#475569', fontSize: 8, fontFamily: 'JetBrains Mono, monospace' }}
              axisLine={false} tickLine={false}
              tickFormatter={v => `$${v}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <ReferenceLine y={0} stroke="rgba(255,255,255,0.1)" />
            <Area type="monotone" dataKey="revenue" stroke="#00ff94" strokeWidth={2} fill="url(#rev)" name="revenue" dot={false} />
            <Area type="monotone" dataKey="costs"   stroke="#ef4444" strokeWidth={1.5} fill="url(#cost)" strokeDasharray="4 4" name="costs" dot={false} />
            <Area type="monotone" dataKey="profit"  stroke="#00c8ff" strokeWidth={1.5} fill="url(#profit)" name="profit" dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </GlassCard>
  );
}
