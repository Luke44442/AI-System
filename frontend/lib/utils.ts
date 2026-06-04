import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import type { AgentStatus, ActivityType, Department } from '@/types';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, compact = false): string {
  if (compact && value >= 1000) {
    return `$${(value / 1000).toFixed(1)}k`;
  }
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value);
}

export function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString('en-US', {
    hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false,
  });
}

export function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60)  return `${s}s ago`;
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  return `${Math.floor(s / 3600)}h ago`;
}

export function scoreGrade(score: number): { grade: string; color: string } {
  if (score >= 85) return { grade: 'A+', color: '#00ff94' };
  if (score >= 75) return { grade: 'A',  color: '#00c8ff' };
  if (score >= 65) return { grade: 'B',  color: '#9333ea' };
  if (score >= 50) return { grade: 'C',  color: '#f59e0b' };
  return             { grade: 'F',  color: '#ef4444' };
}

export function statusColor(status: AgentStatus): string {
  const map: Record<AgentStatus, string> = {
    running:     '#00ff94',
    idle:        '#475569',
    blocked:     '#f59e0b',
    error:       '#ef4444',
    not_started: '#1e293b',
    stopped:     '#334155',
  };
  return map[status] ?? '#475569';
}

export function deptColor(dept: Department | string): string {
  const map: Record<string, string> = {
    executive:        '#f59e0b',
    research:         '#00c8ff',
    strategy:         '#9333ea',
    execution:        '#00ff94',
    finance:          '#10b981',
    self_improvement: '#ec4899',
  };
  return map[dept] ?? '#94a3b8';
}

export function deptLabel(dept: string): string {
  return dept.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
}

export function agentShortName(name: string): string {
  return name.replace('Agent', '').replace(/([A-Z])/g, ' $1').trim();
}

export function activityColor(type: ActivityType): string {
  const map: Record<ActivityType, string> = {
    info:      '#00c8ff',
    success:   '#00ff94',
    warning:   '#f59e0b',
    error:     '#ef4444',
    decision:  '#f59e0b',
    discovery: '#9333ea',
  };
  return map[type] ?? '#94a3b8';
}

export function generateId(): string {
  return Math.random().toString(36).slice(2, 11);
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}
