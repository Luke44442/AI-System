'use client';
import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import { GlassCard, PanelHeader, MetricCard, CyberButton } from '@/components/ui';
import { RevenueChart } from '@/components/panels/RevenueChart';
import { useSystemStore } from '@/store/useSystemStore';
import { revenueApi }     from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { DollarSign, TrendingUp, PlusCircle } from 'lucide-react';

// Demo forecast data
const FORECAST_DATA = Array.from({ length: 12 }, (_, i) => ({
  month: ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][i],
  projected: Math.round(500 * Math.pow(1.18, i)),
  actual: i < 3 ? Math.round(480 * Math.pow(1.15, i)) : null,
}));

const ROI_DATA = [
  { name: 'AI Newsletter', value: 40, color: '#00ff94' },
  { name: 'SaaS Content',  value: 30, color: '#00c8ff' },
  { name: 'Automation',    value: 20, color: '#9333ea' },
  { name: 'Lead Gen',      value: 10, color: '#f59e0b' },
];

export default function RevenuePage() {
  const { revenue, kpis, revenueHistory } = useSystemStore();
  const [isRecording, setIsRecording] = useState(false);
  const [amount, setAmount] = useState('');
  const [type, setType] = useState<'revenue' | 'cost'>('revenue');

  async function handleRecord() {
    const amt = parseFloat(amount);
    if (isNaN(amt) || amt <= 0) return;
    setIsRecording(true);
    try {
      await revenueApi.record({ amount: amt, entry_type: type, source: 'manual' });
      setAmount('');
    } finally {
      setIsRecording(false);
    }
  }

  const totalRev  = revenue?.total_revenue_usd ?? kpis?.total_revenue_usd ?? 0;
  const totalCost = revenue?.total_costs_usd   ?? kpis?.total_costs_usd   ?? 0;
  const profit    = revenue?.net_profit_usd    ?? (totalRev - totalCost);
  const roi       = revenue?.roi_pct           ?? (totalCost > 0 ? (profit / totalCost) * 100 : 0);
  const projects  = revenue?.active_projects   ?? 0;

  return (
    <div className="flex flex-col gap-3">
      <div className="font-orbitron text-base font-bold text-neon-blue">Revenue Dashboard</div>

      {/* KPI row */}
      <div className="grid grid-cols-5 gap-3">
        <MetricCard label="Total Revenue"  value={formatCurrency(totalRev)}   color="#00ff94" icon="$" />
        <MetricCard label="Total Costs"    value={formatCurrency(totalCost)}  color="#ef4444" icon="↓" />
        <MetricCard label="Net Profit"     value={formatCurrency(profit)}     color={profit >= 0 ? '#00ff94' : '#ef4444'} icon="↑" />
        <MetricCard label="ROI"            value={`${roi.toFixed(1)}%`}       color="#00c8ff" icon="%" />
        <MetricCard label="Active Projects" value={String(projects)}           color="#9333ea" icon="◈" />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-3 gap-3" style={{ minHeight: 300 }}>
        {/* Revenue + cost timeline */}
        <div className="col-span-2" style={{ minHeight: 300 }}>
          <RevenueChart />
        </div>

        {/* Project allocation pie */}
        <GlassCard noPad>
          <PanelHeader title="Revenue Allocation" badgeColor="#9333ea" icon={<DollarSign size={12} />} />
          <div className="p-3" style={{ height: 250 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={ROI_DATA} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                  paddingAngle={4} dataKey="value">
                  {ROI_DATA.map((entry, i) => (
                    <Cell key={i} fill={entry.color} stroke="transparent"
                      style={{ filter: `drop-shadow(0 0 6px ${entry.color}80)` }} />
                  ))}
                </Pie>
                <Legend
                  formatter={(value) => (
                    <span className="font-mono text-[9px] text-slate-400">{value}</span>
                  )}
                />
                <Tooltip
                  contentStyle={{ background: '#0d1b2e', border: '1px solid rgba(0,200,255,0.2)', borderRadius: 6 }}
                  labelStyle={{ color: '#00c8ff', fontFamily: 'monospace', fontSize: 10 }}
                  itemStyle={{ color: '#94a3b8', fontFamily: 'monospace', fontSize: 10 }}
                  formatter={(v: number) => [`${v}%`, '']}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>
      </div>

      {/* 12-month forecast */}
      <GlassCard noPad>
        <PanelHeader title="12-Month Revenue Forecast" badge="PROJECTED" badgeColor="#f59e0b" icon={<TrendingUp size={12} />} />
        <div className="p-4" style={{ height: 220 }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={FORECAST_DATA}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,200,255,0.06)" />
              <XAxis dataKey="month" tick={{ fill: '#475569', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#475569', fontSize: 9, fontFamily: 'JetBrains Mono, monospace' }} axisLine={false} tickLine={false} tickFormatter={v => `$${v}`} />
              <Tooltip
                contentStyle={{ background: '#0d1b2e', border: '1px solid rgba(0,200,255,0.2)', borderRadius: 6 }}
                labelStyle={{ color: '#00c8ff', fontFamily: 'monospace', fontSize: 10 }}
                formatter={(v: number, name) => [formatCurrency(v), name]}
              />
              <Bar dataKey="projected" fill="#00c8ff" fillOpacity={0.3} stroke="#00c8ff" strokeWidth={1} radius={[2,2,0,0]} name="Projected" />
              <Bar dataKey="actual"    fill="#00ff94" fillOpacity={0.6} stroke="#00ff94" strokeWidth={1} radius={[2,2,0,0]} name="Actual" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </GlassCard>

      {/* Manual record */}
      <GlassCard noPad>
        <PanelHeader title="Record Transaction" icon={<PlusCircle size={12} />} />
        <div className="p-4 flex items-center gap-3">
          <input
            type="number"
            value={amount}
            onChange={e => setAmount(e.target.value)}
            placeholder="Amount (USD)"
            className="px-3 py-2 bg-surface-mid/50 border border-[rgba(255,255,255,0.08)] rounded font-mono text-[11px] text-slate-200 placeholder-slate-600 focus:outline-none focus:border-neon-blue/40 w-40"
          />
          <div className="flex gap-1">
            {(['revenue', 'cost'] as const).map(t => (
              <button
                key={t}
                onClick={() => setType(t)}
                className={`font-mono text-[9px] px-3 py-2 rounded-sm transition-all capitalize ${
                  type === t
                    ? t === 'revenue' ? 'bg-neon-green/15 text-neon-green border border-neon-green/25' : 'bg-neon-red/15 text-neon-red border border-neon-red/25'
                    : 'text-slate-500 border border-slate-700'
                }`}
              >
                {t}
              </button>
            ))}
          </div>
          <CyberButton onClick={() => void handleRecord()} loading={isRecording} icon={<PlusCircle size={10} />}>
            Record
          </CyberButton>
        </div>
      </GlassCard>
    </div>
  );
}
