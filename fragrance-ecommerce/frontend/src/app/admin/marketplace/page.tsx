"use client";
/**
 * Marketplace Sync — per-platform listing counts by state, recent failures,
 * and a manual full-catalog sync trigger.
 */
import { useCallback, useEffect, useState } from "react";
import { marketplaceApi, type MarketplaceHealth } from "@/lib/api";
import {
  PageHeader, Card, StatusBadge, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

const PLATFORM_LABEL: Record<string, string> = {
  etsy: "Etsy", ebay: "eBay", tiktok_shop: "TikTok Shop",
  pinterest: "Pinterest", google_merchant: "Google Merchant",
};

export default function MarketplaceSyncPage() {
  const [health, setHealth] = useState<MarketplaceHealth | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    setHealth(await marketplaceApi.status());
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 60_000);
    return () => clearInterval(t);
  }, [load]);

  const syncAll = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await marketplaceApi.syncAll();
      setSyncResult(JSON.stringify(res));
      await load();
    } catch (e) {
      setSyncResult("Sync failed — check System Health for details.");
    } finally {
      setSyncing(false);
    }
  };

  if (!health) return <div className="p-8 text-gray-500 text-sm">Loading marketplace status…</div>;

  const configuredByPlatform: Record<string, boolean> = {};
  for (const p of health.platforms) configuredByPlatform[p.platform] = p.configured;
  const platforms = Array.from(new Set([
    ...health.platforms.map((p) => p.platform),
    ...Object.keys(health.listing_counts),
  ]));

  return (
    <div className="pb-12">
      <PageHeader
        title="Marketplace Sync"
        subtitle={`${health.dead_letter_count} unresolved dead letter(s)`}
        actions={
          <Button variant="primary" onClick={syncAll} disabled={syncing}>
            {syncing ? "Syncing…" : "Sync all products now"}
          </Button>
        }
      />

      {syncResult && (
        <p className="px-8 text-xs text-gray-500 mb-4 break-all">{syncResult}</p>
      )}

      <div className="px-8 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {platforms.map((p) => {
          const counts = health.listing_counts[p] ?? {};
          const published = (counts["published"] ?? 0) + (counts["active"] ?? 0);
          const pending = (counts["pending"] ?? 0) + (counts["retrying"] ?? 0) + (counts["created"] ?? 0);
          const failed = (counts["failed"] ?? 0) + (counts["dead"] ?? 0) + (counts["error"] ?? 0);
          const configured = Boolean(configuredByPlatform[p]);
          return (
            <Card key={p} className="p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-white text-sm">{PLATFORM_LABEL[p] ?? p}</h3>
                <span className={`text-[10px] uppercase tracking-widest ${configured ? "text-emerald-400" : "text-gray-600"}`}>
                  {configured ? "connected" : "not configured"}
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-xl font-light text-emerald-400">{published}</p>
                  <p className="text-[10px] uppercase tracking-widest text-gray-500">Live</p>
                </div>
                <div>
                  <p className="text-xl font-light text-amber-400">{pending}</p>
                  <p className="text-[10px] uppercase tracking-widest text-gray-500">Pending</p>
                </div>
                <div>
                  <p className="text-xl font-light text-red-400">{failed}</p>
                  <p className="text-[10px] uppercase tracking-widest text-gray-500">Failed</p>
                </div>
              </div>
            </Card>
          );
        })}
        {platforms.length === 0 && (
          <Card className="p-5 col-span-full">
            <EmptyState message="No marketplace listings yet. Configure Etsy credentials and run a sync." />
          </Card>
        )}
      </div>

      <div className="px-8 mt-8">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-3">Recent sync failures</h2>
        <Card>
          {health.recent_failures.length === 0 ? (
            <EmptyState message="No sync failures. Everything that should be listed, is." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr><Th>Platform</Th><Th>Status</Th><Th>Attempts</Th><Th>Error</Th><Th>Next retry</Th><Th>Last attempt</Th></tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {health.recent_failures.map((f, i) => (
                  <tr key={i}>
                    <Td>{PLATFORM_LABEL[f.platform] ?? f.platform}</Td>
                    <Td><StatusBadge status={f.status ?? "error"} /></Td>
                    <Td>{f.attempts ?? "—"}</Td>
                    <Td className="max-w-md"><span className="text-xs text-red-400/90 break-words">{f.error ?? "—"}</span></Td>
                    <Td><span className="text-xs">{f.next_retry_at ? timeAgo(f.next_retry_at).replace(" ago", "") : "—"}</span></Td>
                    <Td>{timeAgo(f.last_synced_at)}</Td>
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
