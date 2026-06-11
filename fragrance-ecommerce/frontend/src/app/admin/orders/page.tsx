"use client";
/**
 * Orders — operational view. Each row expands into an event-based lifecycle
 * timeline pulled from system_events, so "where is this order stuck?" is
 * answerable without reading Celery logs.
 */
import { useCallback, useEffect, useState } from "react";
import {
  adminApi, systemApi,
  type AdminOrderRow, type SystemEventRow,
} from "@/lib/api";
import {
  PageHeader, Card, StatusBadge, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

const SEVERITY_DOT: Record<string, string> = {
  info: "bg-gray-500", warning: "bg-amber-400", error: "bg-red-400", critical: "bg-red-500",
};

function Timeline({ orderId }: { orderId: string }) {
  const [events, setEvents] = useState<SystemEventRow[] | null>(null);
  useEffect(() => {
    systemApi.events({ order_id: orderId, limit: 50 }).then((r) => setEvents(r.items));
  }, [orderId]);

  if (!events) return <p className="text-xs text-gray-600 px-6 py-3">Loading timeline…</p>;
  if (events.length === 0) return <p className="text-xs text-gray-600 px-6 py-3">No lifecycle events recorded for this order.</p>;

  return (
    <div className="px-6 py-4 space-y-0">
      {[...events].reverse().map((e, i) => (
        <div key={e.id} className="flex gap-3">
          <div className="flex flex-col items-center">
            <span className={`w-2 h-2 rounded-full mt-1.5 ${SEVERITY_DOT[e.severity] ?? "bg-gray-500"}`} />
            {i < events.length - 1 && <span className="w-px flex-1 bg-[#2a2a2a]" />}
          </div>
          <div className="pb-4">
            <p className="text-xs text-gray-300">
              <code className="text-[#C9A84C]">{e.event_type}</code>
              <span className="text-gray-600 ml-2">{timeAgo(e.created_at)}</span>
            </p>
            {e.message && <p className="text-xs text-gray-500 mt-0.5">{e.message}</p>}
          </div>
        </div>
      ))}
    </div>
  );
}

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<AdminOrderRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [expanded, setExpanded] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const res = await adminApi.orders({
      search: search || undefined,
      status: status || undefined,
      page, page_size: 25,
    });
    setOrders(res.items);
    setTotal(res.total);
    setLoaded(true);
  }, [search, status, page]);

  useEffect(() => { load(); }, [load]);

  const fulfill = async (id: string) => {
    setBusy(id);
    try { await adminApi.fulfillOrder(id); await load(); } finally { setBusy(null); }
  };

  return (
    <div className="pb-12">
      <PageHeader title="Orders" subtitle={`${total} orders across all channels`} />

      <div className="px-8 flex gap-3 mb-4">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search order #, email, name…"
          className="bg-[#141414] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white w-72 focus:border-[#C9A84C] outline-none"
        />
        <select
          value={status}
          onChange={(e) => { setStatus(e.target.value); setPage(1); }}
          className="bg-[#141414] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-gray-300 outline-none"
        >
          <option value="">All statuses</option>
          {["pending", "confirmed", "processing", "shipped", "delivered", "cancelled"].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </div>

      <div className="px-8">
        <Card>
          {!loaded ? (
            <EmptyState message="Loading orders…" />
          ) : orders.length === 0 ? (
            <EmptyState message="No orders match the current filters." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr>
                  <Th>Order</Th><Th>Channel</Th><Th>Status</Th><Th>Payment</Th>
                  <Th>Fulfillment</Th><Th className="text-right">Total</Th><Th />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {orders.map((o) => (
                  <>
                    <tr
                      key={o.id}
                      className="hover:bg-white/[0.02] cursor-pointer"
                      onClick={() => setExpanded(expanded === o.id ? null : o.id)}
                    >
                      <Td>
                        <div className="text-white">{o.order_number}</div>
                        <div className="text-xs text-gray-500">{o.customer_name ?? "Guest"} · {o.item_count} item(s)</div>
                      </Td>
                      <Td><span className="text-xs capitalize">{o.channel.replace("_", " ")}</span></Td>
                      <Td><StatusBadge status={o.status} /></Td>
                      <Td><StatusBadge status={o.payment_status} /></Td>
                      <Td><StatusBadge status={o.fulfillment_status} /></Td>
                      <Td className="text-right text-white">${Number(o.total).toFixed(2)}</Td>
                      <Td>
                        {o.payment_status === "paid" && ["unfulfilled", "processing"].includes(o.fulfillment_status) && (
                          <Button
                            variant="primary"
                            disabled={busy === o.id}
                            onClick={() => fulfill(o.id)}
                          >
                            Run fulfillment
                          </Button>
                        )}
                      </Td>
                    </tr>
                    {expanded === o.id && (
                      <tr key={`${o.id}-timeline`}>
                        <td colSpan={7} className="bg-[#0f0f0f]">
                          <Timeline orderId={o.id} />
                        </td>
                      </tr>
                    )}
                  </>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {total > 25 && (
          <div className="flex justify-end gap-2 mt-4">
            <Button disabled={page === 1} onClick={() => setPage(page - 1)}>Prev</Button>
            <span className="text-xs text-gray-500 self-center">Page {page} of {Math.ceil(total / 25)}</span>
            <Button disabled={page >= Math.ceil(total / 25)} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        )}
      </div>
    </div>
  );
}
