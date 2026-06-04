'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion } from 'framer-motion';
import {
  LayoutDashboard, Bot, Target, DollarSign, MessageSquare,
  Brain, ChevronRight, Zap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSystemStore } from '@/store/useSystemStore';

interface NavItem {
  href: string;
  label: string;
  icon: React.ElementType;
  color: string;
}

const NAV_ITEMS: NavItem[] = [
  { href: '/',              label: 'Dashboard',    icon: LayoutDashboard, color: '#00c8ff' },
  { href: '/agents',        label: 'Agents',       icon: Bot,             color: '#9333ea' },
  { href: '/opportunities', label: 'Opportunities',icon: Target,          color: '#00ff94' },
  { href: '/revenue',       label: 'Revenue',      icon: DollarSign,      color: '#f59e0b' },
  { href: '/chat',          label: 'Agent Chat',   icon: MessageSquare,   color: '#ec4899' },
  { href: '/memory',        label: 'Memory',       icon: Brain,           color: '#00c8ff' },
];

export function Sidebar() {
  const pathname = usePathname();
  const { wsConnected, agents, cycleRunning } = useSystemStore();
  const runningCount = agents.filter(a => a.status === 'running').length;

  return (
    <aside className="relative flex flex-col w-[220px] min-h-screen border-r border-[rgba(0,200,255,0.08)] bg-surface-deep/95 backdrop-blur-xl">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 py-4 border-b border-[rgba(0,200,255,0.08)]">
        <div className="relative w-8 h-8">
          <div className="absolute inset-0 rounded-lg bg-neon-blue/20 border border-neon-blue/30 flex items-center justify-center animate-pulse-slow">
            <Zap size={14} className="text-neon-blue" />
          </div>
        </div>
        <div>
          <div className="font-orbitron text-[11px] font-bold text-neon-blue tracking-wider">AI WEALTH</div>
          <div className="font-mono text-[8px] text-slate-500 tracking-[0.2em]">AUTONOMOUS ENGINE</div>
        </div>
      </div>

      {/* Status strip */}
      <div className="flex items-center gap-3 px-4 py-2.5 border-b border-[rgba(0,200,255,0.05)] bg-surface-mid/30">
        <span className={cn('w-1.5 h-1.5 rounded-full flex-shrink-0', wsConnected ? 'bg-neon-green animate-pulse-slow' : 'bg-slate-600')}
          style={wsConnected ? { boxShadow: '0 0 6px #00ff94' } : {}} />
        <span className="font-mono text-[9px] text-slate-400 tracking-wide">
          {wsConnected ? `${runningCount} agents active` : 'connecting...'}
        </span>
        {cycleRunning && (
          <span className="ml-auto font-mono text-[8px] text-neon-amber animate-pulse-slow">CYCLE</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex flex-col gap-0.5 px-2 py-3 flex-1">
        {NAV_ITEMS.map((item, i) => {
          const isActive = item.href === '/'
            ? pathname === '/'
            : pathname.startsWith(item.href);
          return (
            <motion.div key={item.href} initial={{ opacity: 0, x: -12 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: i * 0.05 }}>
              <Link href={item.href}>
                <div
                  className={cn(
                    'relative flex items-center gap-3 px-3 py-2.5 rounded-md transition-all duration-200 group cursor-pointer',
                    isActive
                      ? 'bg-[rgba(0,200,255,0.08)] border border-[rgba(0,200,255,0.15)]'
                      : 'hover:bg-surface-bright/50 border border-transparent',
                  )}
                >
                  {isActive && (
                    <motion.div
                      className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-5 rounded-r"
                      style={{ background: item.color, boxShadow: `0 0 8px ${item.color}` }}
                      layoutId="activeIndicator"
                    />
                  )}
                  <item.icon
                    size={15}
                    style={{ color: isActive ? item.color : '#475569' }}
                    className={cn('transition-colors duration-200', !isActive && 'group-hover:text-slate-300')}
                  />
                  <span className={cn(
                    'font-mono text-[11px] tracking-wide transition-colors duration-200',
                    isActive ? 'text-slate-200' : 'text-slate-400 group-hover:text-slate-200',
                  )}>
                    {item.label}
                  </span>
                  {isActive && <ChevronRight size={10} className="ml-auto text-neon-blue/50" />}
                </div>
              </Link>
            </motion.div>
          );
        })}
      </nav>

      {/* Department quick-status */}
      <div className="px-3 pb-4 space-y-1">
        <div className="font-mono text-[8px] text-slate-600 tracking-[0.2em] uppercase mb-2 px-1">DEPARTMENTS</div>
        {[
          { id: 'research',  label: 'Research',    color: '#00c8ff', agents: 5 },
          { id: 'strategy',  label: 'Strategy',    color: '#9333ea', agents: 4 },
          { id: 'execution', label: 'Execution',   color: '#00ff94', agents: 6 },
          { id: 'finance',   label: 'Finance',     color: '#f59e0b', agents: 3 },
        ].map(d => {
          const active = agents.filter(a => a.department === d.id && a.status === 'running').length;
          return (
            <div key={d.id} className="flex items-center gap-2 px-1">
              <span className="w-1.5 h-1.5 rounded-full flex-shrink-0" style={{ background: active > 0 ? d.color : '#1e293b', boxShadow: active > 0 ? `0 0 4px ${d.color}` : undefined }} />
              <span className="font-mono text-[9px] text-slate-500 flex-1">{d.label}</span>
              <span className="font-mono text-[9px]" style={{ color: active > 0 ? d.color : '#334155' }}>{active}/{d.agents}</span>
            </div>
          );
        })}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-[rgba(0,200,255,0.06)]">
        <div className="font-mono text-[8px] text-slate-600 tracking-[0.15em]">
          ETHICAL · LEGAL · AUTOMATED
        </div>
      </div>
    </aside>
  );
}
