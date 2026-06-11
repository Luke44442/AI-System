"use client";
/**
 * System Health — failures only. Answers "what needs a human right now?"
 * Auto-refreshes every 30s so broken syncs and stuck orders surface fast.
 */
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  systemApi,
  type FailuresDashboard,
  type DeadLetterRow,
} from "@/lib/api";
import {
  PageHeader, Card, StatCard, StatusBadge, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

export default function SystemHealthPage() {
  const [data, setData] = useState<FailuresDashboard | null>(null);
  const [deadLetters, setDeadLetters] = useState<DeadLetterRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [failures, dl] = await Promise.all([systemApi.failures(), systemApi.deadLetters()]);
      setData(failures);
      setDeadLetters(dl.items);
      setError(null);
    } catch {
      setError("Failed to load system health — the API itself may be down.");
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, [load]);

  const retryDeadLetter = async (id: string) => {
    setBusy(id);
    try { await systemApi.retryDeadLetter(id); await load(); } finally { setBusy(null); }
  };
  const resolveDeadLetter = async (id: string) => {
    setBusy(id);
    try { await systemApi.resolveDeadLetter(id); await load(); } finally { setBusy(null); }
  };

  if (error) return <div className="p-8 text-red-400 text-sm">{error}</div>;
  if (!data) return <div className="p-8 text-gray-500 text-sm">Loading system health…</div>;

  const c = data.counts;

  return (
    <div className="pb-12">
      <PageHeader
        title="System Health"
        subtitle="Failures and human-action queues only — refreshed every 30s"
        actions={
          <div className="flex items-center gap-2">
            <span className={`w-2.5 h-2.5 rounded-full ${data.healthy ? "bg-emerald-400" : "bg-red-500 animate-pulse"}`} />
            <span className={`text-xs ${data.healthy ? "text-emerald-400" : "text-red-400"}`}>
              {data.healthy ? "All systems nominal" : "Attention required"}
            </span>
          </div>
        }
      />

      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 px-8">
        <StatCard label="Failed supplier orders" value={c.failed_supplier_orders} tone={c.failed_supplier_orders ? "bad" : "good"} />
        <StatCard label="Supplier queue backlog" value={c.supplier_queue_backlog} tone={c.supplier_queue_backlog ? "warn" : "good"} />
        <StatCard label="Dead-letter listings" value={c.dead_letter_listings} tone={c.dead_letter_listings ? "bad" : "good"} />
        <StatCard label="Retrying listings" value={c.retrying_listings} tone={c.retrying_listings ? "warn" : "good"} />
        <StatCard label="Orphaned paid orders" value={c.orphaned_paid_orders} tone={c.orphaned_paid_orders ? "bad" : "good"} />
      </div>

      {(c.supplier_queue_backlog > 0 || c.failed_supplier_orders > 0) && (
        <div className="px-8 mt-4">
          <Link href="/admin/supplier-queue" className="text-xs text-[#C9A84C] hover:underline">
            → Open the supplier queue to act on {c.supplier_queue_backlog + c.failed_supplier_orders} order(s)
          </Link>
        </div>
      )}

      {/* Dead letters */}
      <div className="px-8 mt-8">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-3">Dead-letter listings</h2>
        <Card>
          {deadLetters.length === 0 ? (
            <EmptyState message="No dead-lettered listings. Retries are keeping up." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr>
                  <Th>Platform</Th><Th>Operation</Th><Th>Attempts</Th><Th>Last error</Th><Th>Age</Th><Th />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {deadLetters.map((d) => (
                  <tr key={d.id}>
                    <Td><StatusBadge status={d.platform} /></Td>
                    <Td>{d.operation}</Td>
                    <Td>{d.attempts}</Td>
                    <Td className="max-w-md"><span className="text-red-400/90 text-xs break-words">{d.last_error ?? "—"}</span></Td>
                    <Td>{timeAgo(d.created_at)}</Td>
                    <Td>
                      <div className="flex gap-2 justify-end">
                        <Button onClick={() => retryDeadLetter(d.id)} disabled={busy === d.id} variant="primary">Retry</Button>
                        <Button onClick={() => resolveDeadLetter(d.id)} disabled={busy === d.id}>Dismiss</Button>
                      </div>
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      {/* Recent error events */}
      <div className="px-8 mt-8">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-3">Recent errors</h2>
        <Card>
          {data.recent_errors.length === 0 ? (
            <EmptyState message="No recent error events." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr><Th>Severity</Th><Th>Event</Th><Th>Message</Th><Th>When</Th></tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {data.recent_errors.map((e) => (
                  <tr key={e.id}>
                    <Td><StatusBadge status={e.severity} /></Td>
                    <Td><code className="text-xs text-gray-400">{e.event_type}</code></Td>
                    <Td className="max-w-lg"><span className="text-xs break-words">{e.message ?? "—"}</span></Td>
                    <Td>{timeAgo(e.created_at)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>
    </div>
  );
}
