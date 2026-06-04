import { getAuthSession } from '@/lib/auth';
import { getUserSubscription, PLANS } from '@/lib/stripe';
import { BillingClient } from '@/components/dashboard/BillingClient';
import { CreditCard } from 'lucide-react';

export default async function BillingPage() {
  const session = await getAuthSession();
  const { tier, subscription, plan } = await getUserSubscription(session!.user.id);

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-2">
          <CreditCard size={22} className="text-amber-400" />
          Billing & Plans
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          Manage your subscription and usage limits.
        </p>
      </div>

      {/* Current plan */}
      <div className="glass p-5 rounded-2xl">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">Current plan</p>
            <div className="flex items-center gap-3">
              <span className="text-xl font-bold text-white">{plan.name}</span>
              {tier !== 'free' && (
                <span className="text-xs text-emerald-400 bg-emerald-400/10 border border-emerald-400/20 px-2 py-0.5 rounded-full">
                  Active
                </span>
              )}
            </div>
            {subscription?.currentPeriodEnd && (
              <p className="text-xs text-slate-500 mt-1">
                Renews {new Date(subscription.currentPeriodEnd).toLocaleDateString()}
              </p>
            )}
          </div>
          <div className="text-right">
            <span className="text-3xl font-bold text-white">${plan.price}</span>
            {plan.price > 0 && <span className="text-slate-400 text-sm">/mo</span>}
          </div>
        </div>
      </div>

      <BillingClient currentTier={tier} plans={PLANS} />
    </div>
  );
}
