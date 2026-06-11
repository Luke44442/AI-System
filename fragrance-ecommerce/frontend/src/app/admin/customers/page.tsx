"use client";
/** Customers — back-office customer list with lifetime value. */
import { useCallback, useEffect, useState } from "react";
import { adminApi } from "@/lib/api";
import {
  PageHeader, Card, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

type CustomerRow = Awaited<ReturnType<typeof adminApi.customers>>["items"][number];

export default function AdminCustomersPage() {
  const [items, setItems] = useState<CustomerRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const res = await adminApi.customers({ search: search || undefined, page, page_size: 50 });
    setItems(res.items);
    setTotal(res.total);
    setLoaded(true);
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  return (
    <div className="pb-12">
      <PageHeader title="Customers" subtitle={`${total} registered customers`} />

      <div className="px-8 mb-4">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search by email or name…"
          className="bg-[#141414] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white w-72 focus:border-[#C9A84C] outline-none"
        />
      </div>

      <div className="px-8">
        <Card>
          {!loaded ? (
            <EmptyState message="Loading customers…" />
          ) : items.length === 0 ? (
            <EmptyState message="No customers found." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr>
                  <Th>Customer</Th><Th className="text-right">Orders</Th>
                  <Th className="text-right">Lifetime spend</Th>
                  <Th>Marketing</Th><Th>Joined</Th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {items.map((c) => (
                  <tr key={c.id} className="hover:bg-white/[0.02]">
                    <Td>
                      <div className="text-white text-sm">
                        {[c.first_name, c.last_name].filter(Boolean).join(" ") || "—"}
                      </div>
                      <div className="text-xs text-gray-500">{c.email}</div>
                    </Td>
                    <Td className="text-right">{c.order_count}</Td>
                    <Td className="text-right text-white">${Number(c.total_spent).toFixed(2)}</Td>
                    <Td>
                      <span className={`text-xs ${c.marketing_consent ? "text-emerald-400" : "text-gray-600"}`}>
                        {c.marketing_consent ? "opted in" : "opted out"}
                      </span>
                    </Td>
                    <Td>{timeAgo(c.created_at)}</Td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </Card>

        {total > 50 && (
          <div className="flex justify-end gap-2 mt-4">
            <Button disabled={page === 1} onClick={() => setPage(page - 1)}>Prev</Button>
            <span className="text-xs text-gray-500 self-center">Page {page} of {Math.ceil(total / 50)}</span>
            <Button disabled={page >= Math.ceil(total / 50)} onClick={() => setPage(page + 1)}>Next</Button>
          </div>
        )}
      </div>
    </div>
  );
}
