"use client";
/**
 * Supplier Queue — the human fallback control center.
 * Orders the automation couldn't place land here with a reason; an operator
 * can retry the automated path or record a manual placement.
 */
import { useCallback, useEffect, useState } from "react";
import { systemApi, type SupplierQueueItem } from "@/lib/api";
import {
  PageHeader, Card, StatusBadge, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

const FILTERS = ["all", "manual_queue", "failed", "placed", "shipped"] as const;

export default function SupplierQueuePage() {
  const [items, setItems] = useState<SupplierQueueItem[]>([]);
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [busy, setBusy] = useState<string | null>(null);
  const [resolving, setResolving] = useState<SupplierQueueItem | null>(null);
  const [externalId, setExternalId] = useState("");
  const [note, setNote] = useState("");
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const res = await systemApi.supplierQueue(filter === "all" ? undefined : filter);
    setItems(res.items);
    setLoaded(true);
  }, [filter]);

  useEffect(() => {
    load();
    const t = setInterval(load, 30_000);
    return () => clearInterval(t);
  }, [load]);

  const retry = async (id: string) => {
    setBusy(id);
    try { await systemApi.retryQueueItem(id); await load(); } finally { setBusy(null); }
  };

  const submitResolve = async () => {
    if (!resolving) return;
    setBusy(resolving.id);
    try {
      await systemApi.resolveQueueItem(resolving.id, externalId || undefined, note || undefined);
      setResolving(null); setExternalId(""); setNote("");
      await load();
    } finally { setBusy(null); }
  };

  return (
    <div className="pb-12">
      <PageHeader
        title="Supplier Queue"
        subtitle="Orders awaiting supplier action — every order here needs either a retry or a manual placement"
      />

      <div className="px-8 flex gap-2 mb-4">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1 rounded text-xs border transition-colors ${
              filter === f
                ? "bg-[#C9A84C]/10 text-[#C9A84C] border-[#C9A84C]/40"
                : "text-gray-500 border-[#2a2a2a] hover:text-gray-300"
            }`}
          >
            {f.replace("_", " ")}
          </button>
        ))}
      </div>

      <div className="px-8">
        <Card>
          {!loaded ? (
            <EmptyState message="Loading queue…" />
          ) : items.length === 0 ? (
            <EmptyState message="Queue is empty — all supplier orders are flowing automatically." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr>
                  <Th>Order</Th><Th>Status</Th><Th>Reason</Th><Th>Attempts</Th>
                  <Th>Supplier order</Th><Th>Age</Th><Th />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {items.map((it) => (
                  <tr key={it.id}>
                    <Td>
                      <div className="text-white">{it.order_number ?? it.order_id.slice(0, 8)}</div>
                      <div className="text-xs text-gray-500">
                        {it.customer_name ?? "Guest"} · ${it.order_total ?? "—"}
                      </div>
                    </Td>
                    <Td><StatusBadge status={it.status} /></Td>
                    <Td className="max-w-sm">
                      <span className="text-xs text-amber-400/90 break-words">
                        {it.failure_reason ?? it.queued_reason ?? "—"}
                      </span>
                    </Td>
                    <Td>{it.attempts}</Td>
                    <Td>
                      {it.external_order_id
                        ? <code className="text-xs text-gray-400">{it.external_order_id}</code>
                        : <span className="text-gray-600 text-xs">not placed</span>}
                    </Td>
                    <Td>{timeAgo(it.created_at)}</Td>
                    <Td>
                      {(it.status === "manual_queue" || it.status === "failed" || it.status === "pending") && (
                        <div className="flex gap-2 justify-end">
                          <Button variant="primary" disabled={busy === it.id} onClick={() => retry(it.id)}>
                            Retry auto
                          </Button>
                          <Button disabled={busy === it.id} onClick={() => setResolving(it)}>
                            Mark placed
                          </Button>
                        </div>
                      )}
                    </Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>
      </div>

      {/* Resolve modal */}
      {resolving && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50" onClick={() => setResolving(null)}>
          <div className="bg-[#141414] border border-[#2a2a2a] rounded-lg p-6 w-[420px]" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-white text-sm mb-1">Mark {resolving.order_number} as manually placed</h3>
            <p className="text-xs text-gray-500 mb-4">
              Use this after you placed the order on the supplier's site yourself.
            </p>
            <label className="block text-[11px] uppercase tracking-widest text-gray-500 mb-1">
              Supplier order ID (optional)
            </label>
            <input
              value={externalId}
              onChange={(e) => setExternalId(e.target.value)}
              className="w-full bg-[#0f0f0f] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white mb-3 focus:border-[#C9A84C] outline-none"
              placeholder="e.g. CJ12345678"
            />
            <label className="block text-[11px] uppercase tracking-widest text-gray-500 mb-1">Note</label>
            <input
              value={note}
              onChange={(e) => setNote(e.target.value)}
              className="w-full bg-[#0f0f0f] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white mb-4 focus:border-[#C9A84C] outline-none"
              placeholder="Placed manually via supplier portal"
            />
            <div className="flex justify-end gap-2">
              <Button onClick={() => setResolving(null)}>Cancel</Button>
              <Button variant="primary" onClick={submitResolve} disabled={busy === resolving.id}>
                Confirm placement
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
