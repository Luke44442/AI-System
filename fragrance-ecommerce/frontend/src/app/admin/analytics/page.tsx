"use client";
import { useEffect, useState, useCallback } from "react";
import {
  analyticsApi,
  type ProfitDashboard,
  type ProfitabilityRow,
  type PricingAlert,
} from "@/lib/api";
import { ArrowPathIcon, CheckCircleIcon, ExclamationTriangleIcon } from "@heroicons/react/24/outline";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function fmt(n: number, decimals = 2) {
  return n.toLocaleString("en-US", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}
function fmtCurrency(n: number) {
  return "$" + fmt(n);
}
function fmtPct(n: number) {
  return fmt(n, 1) + "%";
}

// ---------------------------------------------------------------------------
// Sparkline SVG (inline, no deps)
// ---------------------------------------------------------------------------
function Sparkline({ data, color = "#C9A84C", height = 40 }: { data: number[]; color?: string; height?: number }) {
  if (data.length < 2) return null;
  const w = 160;
  const h = height;
  const pad = 4;
  const max = Math.max(...data, 1);
  const min = Math.min(...data, 0);
  const range = max - min || 1;
  const pts = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg width={w} height={h} className="opacity-80">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------
function MetricCard({
  label, value, sub, trend, sparkData, accent = false,
}: {
  label: string; value: string; sub?: string; trend?: number;
  sparkData?: number[]; accent?: boolean;
}) {
  return (
    <div className={`rounded-lg p-5 border ${accent ? "bg-[#C9A84C]/5 border-[#C9A84C]/30" : "bg-[#141414] border-[#1e1e1e]"}`}>
      <p className="text-[11px] uppercase tracking-widest text-gray-500 mb-1">{label}</p>
      <p className={`text-2xl font-light ${accent ? "text-[#C9A84C]" : "text-white"}`}>{value}</p>
      {sub && <p className="text-xs text-gray-500 mt-1">{sub}</p>}
      {trend !== undefined && (
        <p className={`text-xs mt-1 ${trend >= 0 ? "text-emerald-400" : "text-red-400"}`}>
          {trend >= 0 ? "▲" : "▼"} {Math.abs(trend).toFixed(1)}%
        </p>
      )}
      {sparkData && sparkData.length > 1 && (
        <div className="mt-3">
          <Sparkline data={sparkData} color={accent ? "#C9A84C" : "#6b7280"} />
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Channel breakdown
// ---------------------------------------------------------------------------
function ChannelBreakdown({ data }: {
  data: Record<string, { revenue: number; profit: number; orders: number }>;
}) {
  const entries = Object.entries(data).sort((a, b) => b[1].revenue - a[1].revenue);
  const maxRev = Math.max(...entries.map(([, v]) => v.revenue), 1);
  const CHANNEL_COLORS: Record<string, string> = {
    website: "#C9A84C", etsy: "#F1641E", ebay: "#E53238",
    tiktok_shop: "#010101", pinterest: "#E60023", facebook: "#1877F2",
  };
  return (
    <div className="space-y-3">
      {entries.map(([ch, v]) => (
        <div key={ch}>
          <div className="flex justify-between text-xs text-gray-400 mb-1">
            <span className="capitalize">{ch.replace("_", " ")}</span>
            <span>{fmtCurrency(v.revenue)} · {v.orders} orders</span>
          </div>
          <div className="h-2 bg-[#1e1e1e] rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all"
              style={{ width: `${(v.revenue / maxRev) * 100}%`, background: CHANNEL_COLORS[ch] ?? "#6b7280" }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Revenue trend from orders (aggregated by day)
// ---------------------------------------------------------------------------
function RevenueTrend({ orders }: { orders: ProfitabilityRow[] }) {
  const buckets: Record<string, { rev: number; profit: number }> = {};
  orders.forEach((o) => {
    const day = o.order_date ? o.order_date.slice(0, 10) : "unknown";
    if (!buckets[day]) buckets[day] = { rev: 0, profit: 0 };
    buckets[day].rev += o.revenue;
    buckets[day].profit += o.net_profit;
  });
  const days = Object.keys(buckets).sort().slice(-30);
  if (days.length < 2) return <p className="text-gray-600 text-sm">Not enough data.</p>;

  const revData = days.map((d) => buckets[d].rev);
  const profitData = days.map((d) => buckets[d].profit);
  const maxVal = Math.max(...revData, 1);

  const W = 560; const H = 140; const PAD = 24;
  function line(data: number[], color: string) {
    const pts = data.map((v, i) => {
      const x = PAD + (i / (data.length - 1)) * (W - PAD * 2);
      const y = H - PAD - (v / maxVal) * (H - PAD * 2);
      return `${x},${y}`;
    }).join(" ");
    return <polyline key={color} points={pts} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />;
  }

  return (
    <div className="overflow-x-auto">
      <svg width={W} height={H} className="w-full">
        {/* grid lines */}
        {[0.25, 0.5, 0.75, 1].map((f) => (
          <line key={f} x1={PAD} x2={W - PAD}
            y1={H - PAD - f * (H - PAD * 2)} y2={H - PAD - f * (H - PAD * 2)}
            stroke="#1e1e1e" strokeWidth="1" />
        ))}
        {line(revData, "#C9A84C")}
        {line(profitData, "#34d399")}
      </svg>
      <div className="flex gap-6 mt-2 text-xs text-gray-500">
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-[#C9A84C] inline-block" /> Revenue</span>
        <span className="flex items-center gap-1"><span className="w-3 h-0.5 bg-emerald-400 inline-block" /> Net Profit</span>
        <span className="ml-auto">{days[0]} → {days[days.length - 1]}</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Pricing Alerts panel
// ---------------------------------------------------------------------------
function AlertsPanel({ alerts, onResolve }: { alerts: PricingAlert[]; onResolve: (id: string) => void }) {
  const active = alerts.filter((a) => !a.is_resolved);
  if (!active.length)
    return <p className="text-sm text-gray-600">No active pricing alerts.</p>;
  return (
    <div className="space-y-2">
      {active.map((a) => (
        <div key={a.id} className="flex items-start gap-3 p-3 rounded bg-[#1a1a1a] border border-[#252525]">
          <ExclamationTriangleIcon className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
          <div className="flex-1 min-w-0">
            <p className="text-xs text-gray-300 leading-relaxed">{a.message}</p>
            <p className="text-[10px] text-gray-600 mt-0.5 capitalize">{a.alert_type.replace("_", " ")}</p>
          </div>
          <button
            onClick={() => onResolve(a.id)}
            className="shrink-0 text-[10px] text-gray-500 hover:text-emerald-400 transition-colors"
          >
            Resolve
          </button>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Orders table
// ---------------------------------------------------------------------------
function OrdersTable({ orders }: { orders: ProfitabilityRow[] }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-[#1e1e1e] text-[10px] uppercase tracking-widest text-gray-500">
            {["Order", "Date", "Channel", "Revenue", "Net Profit", "Margin"].map((h) => (
              <th key={h} className="pb-2 text-left font-normal pr-4">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {orders.slice(0, 20).map((o) => (
            <tr key={o.order_id} className="border-b border-[#141414] hover:bg-[#141414] transition-colors">
              <td className="py-2 pr-4 font-mono text-xs text-gray-300">{o.order_number}</td>
              <td className="py-2 pr-4 text-gray-500 text-xs">{o.order_date?.slice(0, 10)}</td>
              <td className="py-2 pr-4">
                <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#1e1e1e] text-gray-400 capitalize">
                  {o.channel}
                </span>
              </td>
              <td className="py-2 pr-4 text-gray-200">{fmtCurrency(o.revenue)}</td>
              <td className={`py-2 pr-4 ${o.net_profit >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {fmtCurrency(o.net_profit)}
              </td>
              <td className={`py-2 ${o.margin_pct >= 30 ? "text-emerald-400" : o.margin_pct >= 15 ? "text-amber-400" : "text-red-400"}`}>
                {fmtPct(o.margin_pct)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main page
// ---------------------------------------------------------------------------
export default function AnalyticsDashboard() {
  const [dashboard, setDashboard] = useState<ProfitDashboard | null>(null);
  const [profitability, setProfitability] = useState<{ items: ProfitabilityRow[]; summary: any } | null>(null);
  const [alerts, setAlerts] = useState<PricingAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    setRefreshing(true);
    try {
      const [dash, prof, alertsData] = await Promise.all([
        analyticsApi.dashboard().catch(() => null),
        analyticsApi.profitability({ limit: 100 }).catch(() => null),
        analyticsApi.pricingAlerts().catch(() => ({ items: [] })),
      ]);
      setDashboard(dash);
      setProfitability(prof);
      setAlerts(alertsData?.items ?? []);
      setError(null);
    } catch (e: any) {
      setError("Could not load analytics. Check that the API is running.");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const resolveAlert = async (id: string) => {
    try {
      await analyticsApi.resolveAlert(id);
      setAlerts((prev) => prev.map((a) => a.id === id ? { ...a, is_resolved: true } : a));
    } catch {}
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full min-h-[400px]">
        <div className="text-center">
          <div className="w-6 h-6 border-2 border-[#C9A84C] border-t-transparent rounded-full animate-spin mx-auto mb-3" />
          <p className="text-gray-600 text-sm">Loading analytics…</p>
        </div>
      </div>
    );
  }

  const d = dashboard;
  const orders = profitability?.items ?? [];
  const summary = profitability?.summary;
  const dailyRev = (() => {
    const b: Record<string, number> = {};
    orders.forEach((o) => { const day = o.order_date?.slice(0, 10) ?? ""; b[day] = (b[day] ?? 0) + o.revenue; });
    return Object.keys(b).sort().slice(-14).map((k) => b[k]);
  })();

  return (
    <div className="p-8 max-w-[1400px]">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-light text-white tracking-wide">Analytics</h1>
          <p className="text-gray-500 text-sm mt-1">Revenue, profitability, and pricing intelligence</p>
        </div>
        <button
          onClick={load}
          disabled={refreshing}
          className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors"
        >
          <ArrowPathIcon className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`} />
          Refresh
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 rounded bg-red-900/20 border border-red-800 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* KPI row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard
          label="Revenue (7d)" value={fmtCurrency(d?.revenue_7d ?? 0)}
          sub={`${d?.orders_7d ?? 0} orders`} sparkData={dailyRev} accent
        />
        <MetricCard
          label="Revenue (30d)" value={fmtCurrency(d?.revenue_30d ?? 0)}
          sub={`${d?.orders_30d ?? 0} orders`}
        />
        <MetricCard
          label="Net Profit (30d)" value={fmtCurrency(d?.profit_30d ?? 0)}
        />
        <MetricCard
          label="Avg Margin (30d)" value={fmtPct(d?.avg_margin_30d ?? 0)}
          accent={d !== null && (d.avg_margin_30d ?? 0) >= 30}
        />
      </div>

      {/* Two-column layout */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
        {/* Revenue trend — 2/3 width */}
        <div className="xl:col-span-2 bg-[#141414] rounded-lg border border-[#1e1e1e] p-6">
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-4">Revenue vs Profit Trend</h2>
          <RevenueTrend orders={orders} />
        </div>

        {/* Channel breakdown — 1/3 width */}
        <div className="bg-[#141414] rounded-lg border border-[#1e1e1e] p-6">
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-4">Revenue by Channel</h2>
          {summary?.by_channel && Object.keys(summary.by_channel).length > 0
            ? <ChannelBreakdown data={summary.by_channel} />
            : <p className="text-sm text-gray-600">No channel data yet.</p>
          }
          {summary && (
            <div className="mt-4 pt-4 border-t border-[#1e1e1e] grid grid-cols-2 gap-2">
              <div>
                <p className="text-[10px] text-gray-600 uppercase tracking-widest">Total Revenue</p>
                <p className="text-white text-sm">{fmtCurrency(summary.total_revenue)}</p>
              </div>
              <div>
                <p className="text-[10px] text-gray-600 uppercase tracking-widest">Total Profit</p>
                <p className="text-emerald-400 text-sm">{fmtCurrency(summary.total_profit)}</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Bottom row */}
      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Recent orders — 2/3 */}
        <div className="xl:col-span-2 bg-[#141414] rounded-lg border border-[#1e1e1e] p-6">
          <h2 className="text-xs uppercase tracking-widest text-gray-500 mb-4">Recent Orders — Profitability</h2>
          {orders.length > 0
            ? <OrdersTable orders={orders} />
            : <p className="text-sm text-gray-600">No order data yet.</p>
          }
        </div>

        {/* Pricing alerts — 1/3 */}
        <div className="bg-[#141414] rounded-lg border border-[#1e1e1e] p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xs uppercase tracking-widest text-gray-500">Pricing Alerts</h2>
            {alerts.filter((a) => !a.is_resolved).length > 0 && (
              <span className="text-[10px] bg-amber-400/20 text-amber-400 px-2 py-0.5 rounded-full">
                {alerts.filter((a) => !a.is_resolved).length} active
              </span>
            )}
          </div>
          <AlertsPanel alerts={alerts} onResolve={resolveAlert} />
        </div>
      </div>
    </div>
  );
}
