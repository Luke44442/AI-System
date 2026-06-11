"use client";
/** Email — subscriber stats, automation triggers, SMTP test. */
import { useCallback, useEffect, useState } from "react";
import { emailAdminApi, type EmailSubscriberRow } from "@/lib/api";
import {
  PageHeader, Card, StatCard, Th, Td, Button, EmptyState, timeAgo,
} from "@/components/admin/ui";

const AUTOMATIONS = [
  { id: "cart-abandonment", label: "Cart abandonment", desc: "Emails idle carts (1–25h old). Runs hourly." },
  { id: "review-requests", label: "Review requests", desc: "Asks for reviews 7 days after fulfillment. Daily." },
  { id: "win-back", label: "Win-back", desc: "Re-engages customers inactive 90 days. Daily." },
] as const;

export default function AdminEmailPage() {
  const [counts, setCounts] = useState<{ total: number; subscribed: number; unsubscribed: number; bounced: number } | null>(null);
  const [subs, setSubs] = useState<EmailSubscriberRow[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [testTo, setTestTo] = useState("");

  const load = useCallback(async () => {
    const [c, s] = await Promise.all([
      emailAdminApi.subscriberCount(),
      emailAdminApi.subscribers({ limit: 25 }),
    ]);
    setCounts(c);
    setSubs(s.items);
  }, []);

  useEffect(() => { load(); }, [load]);

  const run = async (id: (typeof AUTOMATIONS)[number]["id"]) => {
    setBusy(id);
    setMessage(null);
    try {
      const res = await emailAdminApi.runAutomation(id);
      setMessage(`${id} queued (task ${res.task_id.slice(0, 8)}…)`);
    } catch {
      setMessage(`${id} failed to queue — is the Celery worker running?`);
    } finally { setBusy(null); }
  };

  const sendTest = async () => {
    if (!testTo) return;
    setBusy("test");
    setMessage(null);
    try {
      await emailAdminApi.sendTest(testTo);
      setMessage(`Test email sent to ${testTo}`);
    } catch {
      setMessage("Test send failed — check SMTP configuration.");
    } finally { setBusy(null); }
  };

  return (
    <div className="pb-12">
      <PageHeader title="Email" subtitle="Subscribers and lifecycle automations" />

      <div className="px-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Subscribed" value={counts?.subscribed ?? "—"} tone="good" />
        <StatCard label="Unsubscribed" value={counts?.unsubscribed ?? "—"} />
        <StatCard label="Bounced" value={counts?.bounced ?? "—"} tone={counts?.bounced ? "warn" : "neutral"} />
        <StatCard label="Total" value={counts?.total ?? "—"} tone="accent" />
      </div>

      {message && <p className="px-8 mt-4 text-xs text-[#C9A84C]">{message}</p>}

      <div className="px-8 mt-8 grid grid-cols-1 lg:grid-cols-3 gap-4">
        {AUTOMATIONS.map((a) => (
          <Card key={a.id} className="p-5">
            <h3 className="text-white text-sm mb-1">{a.label}</h3>
            <p className="text-xs text-gray-500 mb-4">{a.desc}</p>
            <Button variant="primary" disabled={busy === a.id} onClick={() => run(a.id)}>
              {busy === a.id ? "Queuing…" : "Run now"}
            </Button>
          </Card>
        ))}
      </div>

      <div className="px-8 mt-8">
        <Card className="p-5">
          <h3 className="text-white text-sm mb-3">SMTP test</h3>
          <div className="flex gap-2">
            <input
              value={testTo}
              onChange={(e) => setTestTo(e.target.value)}
              placeholder="you@example.com"
              className="bg-[#0f0f0f] border border-[#2a2a2a] rounded px-3 py-2 text-sm text-white w-72 focus:border-[#C9A84C] outline-none"
            />
            <Button disabled={busy === "test" || !testTo} onClick={sendTest}>Send test email</Button>
          </div>
        </Card>
      </div>

      <div className="px-8 mt-8">
        <h2 className="text-sm text-gray-400 uppercase tracking-widest mb-3">Recent subscribers</h2>
        <Card>
          {subs.length === 0 ? (
            <EmptyState message="No subscribers yet." />
          ) : (
            <table className="w-full">
              <thead className="border-b border-[#1e1e1e]">
                <tr><Th>Email</Th><Th>Status</Th><Th>Source</Th><Th className="text-right">Opens</Th><Th>Subscribed</Th></tr>
              </thead>
              <tbody className="divide-y divide-[#1a1a1a]">
                {subs.map((s) => (
                  <tr key={s.id}>
                    <Td><span className="text-white text-sm">{s.email}</span></Td>
                    <Td><span className={`text-xs ${s.status === "subscribed" ? "text-emerald-400" : "text-gray-500"}`}>{s.status}</span></Td>
                    <Td><span className="text-xs">{s.source ?? "—"}</span></Td>
                    <Td className="text-right">{s.open_count}</Td>
                    <Td>{timeAgo(s.subscribed_at)}</Td>
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
