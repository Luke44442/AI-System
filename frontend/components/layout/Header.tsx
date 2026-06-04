'use client';
import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, RefreshCw, Wifi, WifiOff } from 'lucide-react';
import { useSystemStore } from '@/store/useSystemStore';
import { systemApi } from '@/lib/api';
import { formatCurrency } from '@/lib/utils';
import { CyberButton } from '@/components/ui';

export function Header() {
  const { wsConnected, apiOnline, cycleRunning, kpis, revenue, agents, setCycleRunning, setApiOnline } = useSystemStore();
  const [time, setTime] = useState('');
  const [date, setDate] = useState('');

  useEffect(() => {
    const tick = () => {
      const now = new Date();
      setTime(now.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' }));
      setDate(now.toISOString().split('T')[0]);
    };
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  async function handleStartCycle() {
    setCycleRunning(true);
    try {
      await systemApi.startCycle();
    } finally {
      setTimeout(() => setCycleRunning(false), 5000);
    }
  }

  const totalRevenue = revenue?.total_revenue_usd ?? kpis?.total_revenue_usd ?? 0;
  const oppsFound = kpis?.opportunities_discovered ?? 0;
  const activeAgents = agents.filter(a => a.status === 'running').length;

  const pills = [
    { label: 'REVENUE',   value: formatCurrency(totalRevenue, true), color: '#00ff94' },
    { label: 'OPPS',      value: String(oppsFound),                   color: '#9333ea' },
    { label: 'AGENTS',    value: `${activeAgents}/22`,                 color: '#00c8ff' },
  ];

  return (
    <header className="sticky top-0 z-50 flex items-center justify-between px-6 py-2.5 border-b border-[rgba(0,200,255,0.08)] bg-surface-deep/95 backdrop-blur-xl">
      {/* Left — KPI pills */}
      <div className="flex items-center gap-2">
        {pills.map((p, i) => (
          <motion.div
            key={p.label}
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: i * 0.05 }}
            className="flex items-center gap-1.5 px-3 py-1 border border-[rgba(0,200,255,0.1)] rounded-sm bg-surface-mid/30"
          >
            <span className="font-mono text-[8px] text-slate-500 tracking-wider">{p.label}</span>
            <span className="font-orbitron text-xs font-bold" style={{ color: p.color }}>{p.value}</span>
          </motion.div>
        ))}
      </div>

      {/* Center — Title + time */}
      <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center">
        <div className="font-orbitron text-[11px] font-black tracking-[0.3em] text-neon-blue"
          style={{ textShadow: '0 0 20px rgba(0,200,255,0.6)' }}>
          AUTONOMOUS WEALTH ENGINE
        </div>
        <div className="flex items-center gap-3 mt-0.5">
          <span className="font-mono text-[9px] text-slate-600">{date}</span>
          <span className="font-mono text-[10px] text-neon-blue/60">{time}</span>
        </div>
      </div>

      {/* Right — Controls + status */}
      <div className="flex items-center gap-3">
        {/* WS indicator */}
        <div className="flex items-center gap-1.5">
          {wsConnected
            ? <Wifi size={11} className="text-neon-green" />
            : <WifiOff size={11} className="text-slate-600" />}
          <span className={`font-mono text-[8px] tracking-wider ${wsConnected ? 'text-neon-green' : 'text-slate-600'}`}>
            {wsConnected ? 'LIVE' : 'OFFLINE'}
          </span>
        </div>

        <div className="w-px h-4 bg-slate-700" />

        <CyberButton
          onClick={() => void handleStartCycle()}
          loading={cycleRunning}
          icon={<Play size={10} />}
          className="py-1 text-[9px]"
        >
          RUN CYCLE
        </CyberButton>
      </div>
    </header>
  );
}
