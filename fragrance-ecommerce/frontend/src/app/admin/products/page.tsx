"use client";
/**
 * Products — inventory + per-platform marketplace status at a glance.
 * Marketplace badges are real listing states, not assumptions: green =
 * published, amber = pending/retrying, red = failed/dead, gray = no listing.
 */
import { useCallback, useEffect, useMemo, useState } from "react";
import { adminApi, marketplaceApi, type MarketplaceListingRow } from "@/lib/api";
import type { Product } from "@/types";
import {
  PageHeader, Card, Th, Td, Button, EmptyState,
} from "@/components/admin/ui";

const PLATFORMS = ["etsy", "ebay", "tiktok_shop"];

const STATE_COLOR: Record<string, string> = {
  published: "bg-emerald-400", active: "bg-emerald-400",
  pending: "bg-amber-400", retrying: "bg-amber-400", created: "bg-amber-400", uploaded: "bg-sky-400",
  failed: "bg-red-400", dead: "bg-red-500", error: "bg-red-400",
};

function PlatformDots({ listings }: { listings: Record<string, MarketplaceListingRow | undefined> }) {
  return (
    <div className="flex gap-2">
      {PLATFORMS.map((p) => {
        const l = listings[p];
        const color = l ? (STATE_COLOR[l.status] ?? "bg-gray-600") : "bg-gray-700";
        const label = l ? `${p}: ${l.status}` : `${p}: not listed`;
        return (
          <span key={p} title={label} className="flex items-center gap-1">
            <span className={`w-2 h-2 rounded-full ${color}`} />
            <span className="text-[10px] text-gray-500 uppercase">{p.split("_")[0]}</span>
          </span>
        );
      })}
    </div>
  );
}

export default function AdminProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [listings, setListings] = useState<MarketplaceListingRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const [prods, listingPage] = await Promise.all([
      adminApi.products({ search: search || undefined, page, page_size: 25 }),
      marketplaceApi.listings({ page_size: 100 }),
    ]);
    setProducts(prods.items);
    setTotal(prods.total);
    setListings(listingPage.items);
    setLoaded(true);
  }, [search, page]);

  useEffect(() => { load(); }, [load]);

  const listingsByProduct = useMemo(() => {
    const map: Record<string, Record<string, MarketplaceListingRow>> = {};
    for (const l of listings) {
      (map[l.product_id] ??= {})[l.platform] = l;
    }
    return map;
  }, [listings]);

  const syncNow = async (productId: string) => {
    setBusy(productId);
    try { await marketplaceApi.syncProduct(productId); await load(); } finally { setBusy(null); }
  };

  const marginPct = (p: Product): number | null => {
    if (!p.website_price || !p.supplier_cost) return null;
    return ((p.website_price - p.supplier_cost) / p.website_price) * 100;
  };

  return (
    <div className="pb-12">
      <PageHeader title="Products" subtitle={`${total} products in catalog`} />

      <div className="px-8 mb-4">
        <input
          value={search}
          onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          placeholder="Search products…"
          className="bg-[#141414] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white w-72 focus:border-[#C9A84C] outline-none"
        />
      </div>

      <div className="px-8">
        <Card>
          {!loaded ? (
            <EmptyState message="Loading products…" />
          ) : products.length === 0 ? (
            <EmptyState message="No products found." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr>
                  <Th>Product</Th><Th className="text-right">Price</Th>
                  <Th className="text-right">Margin</Th><Th className="text-right">Stock</Th>
                  <Th>Marketplaces</Th><Th />
                </tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {products.map((p) => {
                  const m = marginPct(p);
                  const img = p.images?.[0]?.url;
                  return (
                    <tr key={p.id} className="hover:bg-white/[0.02]">
                      <Td>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded bg-[#1e1e1e] overflow-hidden flex-shrink-0">
                            {img ? (
                              // eslint-disable-next-line @next/next/no-img-element
                              <img src={img} alt={p.name} className="w-full h-full object-cover" loading="lazy" />
                            ) : (
                              <div className="w-full h-full flex items-center justify-center text-gray-700 text-lg">◇</div>
                            )}
                          </div>
                          <div>
                            <div className="text-white text-sm">{p.name}</div>
                            <div className="text-xs text-gray-500">{p.brand?.name ?? "—"} · {p.sku}</div>
                          </div>
                        </div>
                      </Td>
                      <Td className="text-right text-white">
                        {p.website_price ? `$${Number(p.website_price).toFixed(2)}` : "—"}
                      </Td>
                      <Td className="text-right">
                        {m === null ? <span className="text-gray-600">—</span> : (
                          <span className={m < 15 ? "text-red-400" : m < 30 ? "text-amber-400" : "text-emerald-400"}>
                            {m.toFixed(0)}%
                          </span>
                        )}
                      </Td>
                      <Td className="text-right">
                        <span className={
                          p.inventory_quantity <= 0 ? "text-red-400"
                            : p.inventory_quantity <= 3 ? "text-amber-400" : "text-gray-300"
                        }>
                          {p.inventory_quantity}
                        </span>
                      </Td>
                      <Td><PlatformDots listings={listingsByProduct[p.id] ?? {}} /></Td>
                      <Td>
                        <div className="flex justify-end">
                          <Button disabled={busy === p.id} onClick={() => syncNow(p.id)}>
                            {busy === p.id ? "Syncing…" : "Sync now"}
                          </Button>
                        </div>
                      </Td>
                    </tr>
                  );
                })}
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
