'use client';
import { useState } from 'react';
import { Loader2, Check } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { PLANS } from '@/lib/stripe';

type Plans = typeof PLANS;
type Tier = keyof Plans;

interface Props {
  currentTier: string;
  plans: Plans;
}

const FEATURES: Record<string, string[]> = {
  free: ['5 research runs/month', '10 content generations/month', '3 saved projects', 'Opportunity scoring'],
  pro: ['100 research runs/month', '500 content generations/month', '20 saved projects', 'Competitor analysis', 'All content types'],
  creator_pro: ['Unlimited research runs', 'Unlimited content generation', 'Unlimited projects', 'Advanced trend tracking', 'Export to PDF/CSV', 'Priority support'],
  agency: ['Everything in Creator Pro', 'Team accounts (5 seats)', 'API access', 'Custom integrations', 'Dedicated support'],
};

const TIER_COLOR: Record<string, string> = {
  free: 'border-slate-700',
  pro: 'border-violet-500/40 ring-1 ring-violet-500/20',
  creator_pro: 'border-sky-500/40 ring-1 ring-sky-500/20',
  agency: 'border-amber-500/40 ring-1 ring-amber-500/20',
};

export function BillingClient({ currentTier, plans }: Props) {
  const [loading, setLoading] = useState<string | null>(null);

  async function upgrade(tier: string) {
    setLoading(tier);
    try {
      const res = await fetch('/api/stripe/create-checkout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tier }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      // ignore
    } finally {
      setLoading(null);
    }
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {(Object.entries(plans) as [Tier, Plans[Tier]][]).map(([tier, plan]) => {
        const isCurrent = tier === currentTier;
        const features = FEATURES[tier] ?? [];
        const paidTier = tier !== 'free';

        return (
          <div key={tier} className={cn('glass rounded-2xl p-5 border', TIER_COLOR[tier])}>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <h3 className="text-sm font-bold text-white">{plan.name}</h3>
                {isCurrent && (
                  <span className="text-[9px] bg-violet-500/20 text-violet-300 border border-violet-500/30 px-1.5 py-0.5 rounded-full">
                    Current
                  </span>
                )}
              </div>
              <div className="flex items-baseline gap-1">
                <span className="text-2xl font-bold text-white">${plan.price}</span>
                {plan.price > 0 && <span className="text-slate-500 text-xs">/mo</span>}
              </div>
            </div>

            <ul className="space-y-2 mb-5">
              {features.map(f => (
                <li key={f} className="flex items-start gap-2 text-xs text-slate-400">
                  <Check size={11} className="text-emerald-400 mt-0.5 shrink-0" />
                  {f}
                </li>
              ))}
            </ul>

            {!isCurrent && paidTier && (
              <button
                onClick={() => void upgrade(tier)}
                disabled={loading !== null}
                className="w-full flex items-center justify-center gap-2 bg-violet-600 hover:bg-violet-500 disabled:opacity-50 text-white text-xs font-medium py-2 rounded-lg transition"
              >
                {loading === tier && <Loader2 size={12} className="animate-spin" />}
                Upgrade to {plan.name}
              </button>
            )}
            {isCurrent && (
              <div className="w-full text-center text-xs text-slate-500 py-2">Your current plan</div>
            )}
            {!isCurrent && !paidTier && (
              <div className="w-full text-center text-xs text-slate-600 py-2">Free forever</div>
            )}
          </div>
        );
      })}
    </div>
  );
}
