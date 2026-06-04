'use client';
import { cn } from '@/lib/utils';
import { motion, type HTMLMotionProps } from 'framer-motion';
import React from 'react';

// ─── GlassCard ────────────────────────────────────────────────────────────────

interface GlassCardProps extends React.HTMLAttributes<HTMLDivElement> {
  glow?: 'blue' | 'purple' | 'green' | 'none';
  noPad?: boolean;
}

export function GlassCard({ className, glow = 'none', noPad, children, ...props }: GlassCardProps) {
  const glowClass = {
    blue:   'border-[rgba(0,200,255,0.25)] shadow-neon-blue',
    purple: 'border-[rgba(147,51,234,0.3)] shadow-neon-purple',
    green:  'border-[rgba(0,255,148,0.25)] shadow-neon-green',
    none:   'border-[rgba(0,200,255,0.1)]',
  }[glow];

  return (
    <div
      className={cn(
        'relative rounded-lg border backdrop-blur-xl bg-panel-gradient overflow-hidden',
        'transition-all duration-300',
        glowClass,
        !noPad && 'p-4',
        className,
      )}
      {...props}
    >
      {/* Corner accents */}
      <span className="absolute top-0 left-0 w-3 h-3 border-t border-l border-neon-blue/30 rounded-tl" />
      <span className="absolute bottom-0 right-0 w-3 h-3 border-b border-r border-neon-blue/30 rounded-br" />
      {children}
    </div>
  );
}

// ─── PanelHeader ──────────────────────────────────────────────────────────────

interface PanelHeaderProps {
  title: string;
  badge?: string;
  badgeColor?: string;
  icon?: React.ReactNode;
  right?: React.ReactNode;
}

export function PanelHeader({ title, badge, badgeColor = '#00c8ff', icon, right }: PanelHeaderProps) {
  return (
    <div className="flex items-center justify-between px-4 py-2.5 border-b border-[rgba(0,200,255,0.08)]">
      <div className="flex items-center gap-2">
        {icon && <span className="text-neon-blue opacity-70">{icon}</span>}
        <span className="font-orbitron text-[10px] tracking-[0.2em] font-bold uppercase text-neon-blue">
          {title}
        </span>
      </div>
      <div className="flex items-center gap-2">
        {badge && (
          <span
            className="text-[8px] tracking-[0.15em] px-2 py-0.5 border rounded-sm font-mono animate-pulse-slow"
            style={{ color: badgeColor, borderColor: `${badgeColor}40` }}
          >
            {badge}
          </span>
        )}
        {right}
      </div>
    </div>
  );
}

// ─── MetricCard ───────────────────────────────────────────────────────────────

interface MetricCardProps {
  label: string;
  value: string | number;
  subtext?: string;
  color?: string;
  icon?: string;
  trend?: number;
  className?: string;
}

export function MetricCard({ label, value, subtext, color = '#00c8ff', icon, trend, className }: MetricCardProps) {
  return (
    <GlassCard className={cn('flex flex-col gap-1', className)}>
      <div className="flex items-center justify-between">
        <span className="text-[9px] font-mono tracking-[0.15em] text-slate-400 uppercase">{label}</span>
        {icon && <span className="text-base opacity-60" style={{ color }}>{icon}</span>}
      </div>
      <div className="flex items-end gap-2">
        <span
          className="font-orbitron font-bold text-xl leading-none"
          style={{ color, textShadow: `0 0 12px ${color}60` }}
        >
          {value}
        </span>
        {trend !== undefined && (
          <span className={cn('text-[10px] font-mono mb-0.5', trend >= 0 ? 'text-neon-green' : 'text-neon-red')}>
            {trend >= 0 ? '↑' : '↓'} {Math.abs(trend).toFixed(1)}%
          </span>
        )}
      </div>
      {subtext && <span className="text-[9px] font-mono text-slate-500">{subtext}</span>}
    </GlassCard>
  );
}

// ─── PulsingDot ───────────────────────────────────────────────────────────────

interface PulsingDotProps {
  color?: string;
  size?: number;
  pulse?: boolean;
  className?: string;
}

export function PulsingDot({ color = '#00ff94', size = 8, pulse = true, className }: PulsingDotProps) {
  return (
    <span className={cn('inline-block rounded-full flex-shrink-0', className)} style={{ width: size, height: size, background: color, boxShadow: pulse ? `0 0 ${size}px ${color}` : undefined }}>
      {pulse && (
        <span
          className="absolute rounded-full animate-ping opacity-60"
          style={{ width: size, height: size, background: color }}
        />
      )}
    </span>
  );
}

// ─── NeonBadge ────────────────────────────────────────────────────────────────

interface NeonBadgeProps {
  label: string;
  color?: string;
  size?: 'xs' | 'sm';
  className?: string;
}

export function NeonBadge({ label, color = '#00c8ff', size = 'xs', className }: NeonBadgeProps) {
  return (
    <span
      className={cn(
        'font-mono tracking-wider border rounded-sm uppercase',
        size === 'xs' ? 'text-[8px] px-1.5 py-0.5' : 'text-[10px] px-2 py-1',
        className,
      )}
      style={{ color, borderColor: `${color}40`, background: `${color}10` }}
    >
      {label}
    </span>
  );
}

// ─── ScoreBar ─────────────────────────────────────────────────────────────────

interface ScoreBarProps {
  score: number;
  max?: number;
  label?: string;
  color?: string;
  className?: string;
  showValue?: boolean;
}

export function ScoreBar({ score, max = 100, label, color = '#00c8ff', className, showValue = true }: ScoreBarProps) {
  const pct = Math.round((score / max) * 100);
  return (
    <div className={cn('flex flex-col gap-1', className)}>
      {(label || showValue) && (
        <div className="flex justify-between items-center">
          {label && <span className="text-[9px] font-mono text-slate-400">{label}</span>}
          {showValue && <span className="text-[9px] font-mono" style={{ color }}>{score}</span>}
        </div>
      )}
      <div className="h-1 w-full bg-slate-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full rounded-full"
          style={{ background: `linear-gradient(90deg, ${color}80, ${color})`, boxShadow: `0 0 6px ${color}` }}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        />
      </div>
    </div>
  );
}

// ─── ScoreRing ────────────────────────────────────────────────────────────────

interface ScoreRingProps {
  score: number;
  size?: number;
  stroke?: number;
  color?: string;
  grade?: string;
}

export function ScoreRing({ score, size = 64, stroke = 5, color = '#00c8ff', grade }: ScoreRingProps) {
  const r = (size - stroke * 2) / 2;
  const circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div className="relative flex items-center justify-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size/2} cy={size/2} r={r} fill="none" stroke="#1e293b" strokeWidth={stroke} />
        <motion.circle
          cx={size/2} cy={size/2} r={r}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={circ}
          initial={{ strokeDashoffset: circ }}
          animate={{ strokeDashoffset: circ - dash }}
          transition={{ duration: 1.2, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 4px ${color})` }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="font-orbitron font-bold text-sm leading-none" style={{ color }}>
          {grade ?? score}
        </span>
      </div>
    </div>
  );
}

// ─── AgentAvatar ──────────────────────────────────────────────────────────────

interface AgentAvatarProps {
  name: string;
  status?: string;
  color?: string;
  size?: number;
}

export function AgentAvatar({ name, status, color = '#00c8ff', size = 32 }: AgentAvatarProps) {
  const initials = name
    .replace('Agent', '')
    .split(/(?=[A-Z])/)
    .filter(Boolean)
    .slice(0, 2)
    .map(w => w[0])
    .join('');
  const isRunning = status === 'running';
  return (
    <div
      className="relative flex items-center justify-center rounded-md font-mono text-xs font-bold flex-shrink-0"
      style={{ width: size, height: size, background: `${color}15`, border: `1px solid ${color}40`, color }}
    >
      {initials}
      {isRunning && (
        <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-neon-green animate-pulse-slow"
          style={{ boxShadow: '0 0 4px #00ff94' }} />
      )}
    </div>
  );
}

// ─── MotionItem ───────────────────────────────────────────────────────────────

export function MotionItem({ children, delay = 0, className, ...props }: HTMLMotionProps<'div'> & { delay?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay, ease: 'easeOut' }}
      className={className}
      {...props}
    >
      {children}
    </motion.div>
  );
}

// ─── CyberButton ─────────────────────────────────────────────────────────────

interface CyberButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  loading?: boolean;
  icon?: React.ReactNode;
}

export function CyberButton({ children, variant = 'primary', loading, icon, className, ...props }: CyberButtonProps) {
  const colors = {
    primary:   'border-neon-blue text-neon-blue hover:bg-neon-blue/10 hover:shadow-neon-blue',
    secondary: 'border-slate-600 text-slate-400 hover:border-slate-400 hover:text-slate-200',
    danger:    'border-neon-red text-neon-red hover:bg-neon-red/10',
  };
  return (
    <button
      className={cn(
        'flex items-center gap-2 px-4 py-2 border rounded-sm font-mono text-[10px] tracking-widest uppercase',
        'transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed',
        colors[variant],
        className,
      )}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? (
        <span className="w-3 h-3 border border-current border-t-transparent rounded-full animate-spin" />
      ) : icon}
      {children}
    </button>
  );
}
