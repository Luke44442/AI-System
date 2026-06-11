"use client";
/** Pricing Alerts — margin erosion, competitor undercuts, supplier cost jumps. */
import { useCallback, useEffect, useState } from "react";
import { analyticsApi, type PricingAlert } from "@/lib/api";
import {
  PageHeader, Card, StatusBadge, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

const ALERT_LABEL: Record<string, string> = {
  low_margin: "Low margin",
  competitor_cheaper: "Competitor cheaper",
  cost_increase: "Supplier cost increase",
};

export default function PricingAlertsPage() {
  const [alerts, setAlerts] = useState<PricingAlert[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [loaded, setLoaded] = useState(false);

  const load = useCallback(async () => {
    const res = await analyticsApi.pricingAlerts();
    setAlerts(res.items);
    setLoaded(true);
  }, []);

  useEffect(() => { load(); }, [load]);

  const resolve = async (id: string) => {
    setBusy(id);
    try { await analyticsApi.resolveAlert(id); await load(); } finally { setBusy(null); }
  };

  const open = alerts.filter((a) => !a.is_resolved);

  return (
    <div className="pb-12">
      <PageHeader
        title="Pricing Alerts"
        subtitle={`${open.length} open alert(s) — margin risk surfaced before it costs money`}
      />

      <div className="px-8">
        <Card>
          {!loaded ? (
            <EmptyState message="Loading alerts…" />
          ) : open.length === 0 ? (
            <EmptyState message="No open pricing alerts. Margins are holding." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr><Th>Type</Th><Th>Detail</Th><Th className="text-right">Current</Th><Th className="text-right">Threshold</Th><Th>Raised</Th><Th /></tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {open.map((a) => (
                  <tr key={a.id} className="hover:bg-white/[0.02]">
                    <Td><StatusBadge status={a.alert_type === "low_margin" ? "warning" : "error"} />{" "}
                      <span className="text-xs ml-1">{ALERT_LABEL[a.alert_type] ?? a.alert_type}</span></Td>
                    <Td className="max-w-lg"><span className="text-xs break-words">{a.message}</span></Td>
                    <Td className="text-right">{Number(a.current_value).toFixed(2)}</Td>
                    <Td className="text-right text-gray-500">{Number(a.threshold_value).toFixed(2)}</Td>
                    <Td>{timeAgo(a.created_at)}</Td>
                    <Td>
                      <div className="flex justify-end">
                        <Button disabled={busy === a.id} onClick={() => resolve(a.id)}>Resolve</Button>
                      </div>
                    </Td>
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
