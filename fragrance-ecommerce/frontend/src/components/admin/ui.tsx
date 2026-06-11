"use client";
/**
 * Shared admin design system — dark "trading terminal" aesthetic.
 * Near-black surfaces, muted gold accent, status-coded chips everywhere.
 */
import { ReactNode } from "react";

export const GOLD = "#C9A84C";

export function PageHeader({ title, subtitle, actions }: {
  title: string; subtitle?: string; actions?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between px-8 pt-8 pb-4">
      <div>
        <h1 className="text-xl font-light text-white tracking-wide">{title}</h1>
        {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return (
    <div className={`rounded-lg bg-[#141414] border border-[#1e1e1e] ${className}`}>
      {children}
    </div>
  );
}

export function StatCard({ label, value, tone = "neutral" }: {
  label: string; value: string | number; tone?: "neutral" | "good" | "warn" | "bad" | "accent";
}) {
  const toneClass = {
    neutral: "text-white",
    good: "text-emerald-400",
    warn: "text-amber-400",
    bad: "text-red-400",
    accent: `text-[${GOLD}]`,
  }[tone];
  return (
    <Card className="p-5">
      <p className="text-[11px] uppercase tracking-widest text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-light ${tone === "accent" ? "text-[#C9A84C]" : toneClass}`}>{value}</p>
    </Card>
  );
}

const STATUS_TONES: Record<string, string> = {
  // generic
  active: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  published: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  placed: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  shipped: "bg-sky-500/10 text-sky-400 border-sky-500/30",
  delivered: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  paid: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  fulfilled: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  resolved: "bg-emerald-500/10 text-emerald-400 border-emerald-500/30",
  // in-flight
  pending: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  processing: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  placing: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  retrying: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  created: "bg-gray-500/10 text-gray-400 border-gray-500/30",
  uploaded: "bg-sky-500/10 text-sky-400 border-sky-500/30",
  draft: "bg-gray-500/10 text-gray-400 border-gray-500/30",
  unfulfilled: "bg-gray-500/10 text-gray-400 border-gray-500/30",
  // bad
  failed: "bg-red-500/10 text-red-400 border-red-500/30",
  error: "bg-red-500/10 text-red-400 border-red-500/30",
  dead: "bg-red-500/10 text-red-400 border-red-500/30",
  cancelled: "bg-red-500/10 text-red-400 border-red-500/30",
  critical: "bg-red-500/10 text-red-400 border-red-500/30",
  // queue / info
  manual_queue: "bg-purple-500/10 text-purple-400 border-purple-500/30",
  warning: "bg-amber-500/10 text-amber-400 border-amber-500/30",
  info: "bg-gray-500/10 text-gray-400 border-gray-500/30",
};

export function StatusBadge({ status }: { status: string }) {
  const tone = STATUS_TONES[status] ?? "bg-gray-500/10 text-gray-400 border-gray-500/30";
  return (
    <span className={`inline-block px-2 py-0.5 rounded border text-[11px] font-medium tracking-wide ${tone}`}>
      {status.replace(/_/g, " ")}
    </span>
  );
}

export function Th({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return (
    <th className={`px-4 py-3 text-left text-[10px] uppercase tracking-widest text-gray-500 font-medium ${className}`}>
      {children}
    </th>
  );
}

export function Td({ children, className = "" }: { children?: ReactNode; className?: string }) {
  return <td className={`px-4 py-3 text-sm text-gray-300 ${className}`}>{children}</td>;
}

export function Button({ children, onClick, variant = "secondary", disabled = false }: {
  children: ReactNode; onClick?: () => void;
  variant?: "primary" | "secondary" | "danger"; disabled?: boolean;
}) {
  const styles = {
    primary: "bg-[#C9A84C] text-black hover:bg-[#d9b85c]",
    secondary: "bg-white/5 text-gray-300 border border-[#2a2a2a] hover:bg-white/10",
    danger: "bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20",
  }[variant];
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${styles}`}
    >
      {children}
    </button>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <p className="text-sm text-gray-600 px-4 py-10 text-center">{message}</p>;
}

export function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  return `${Math.floor(s / 86400)}d ago`;
}
