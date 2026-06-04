import Stripe from 'stripe';
import { prisma } from './db';

export const stripe = new Stripe(process.env.STRIPE_SECRET_KEY!, {
  apiVersion: '2025-02-24.acacia',
});

export const PLANS = {
  free: {
    name: 'Free',
    price: 0,
    priceId: null,
    limits: {
      researchRunsPerMonth: 5,
      contentGenerationsPerMonth: 10,
      savedOpportunities: 20,
      projects: 2,
    },
  },
  pro: {
    name: 'Pro',
    price: 29,
    priceId: process.env.STRIPE_PRO_PRICE_ID,
    limits: {
      researchRunsPerMonth: 100,
      contentGenerationsPerMonth: 500,
      savedOpportunities: 500,
      projects: 20,
    },
  },
  creator_pro: {
    name: 'Creator Pro',
    price: 49,
    priceId: process.env.STRIPE_CREATOR_PRO_PRICE_ID,
    limits: {
      researchRunsPerMonth: -1,   // unlimited
      contentGenerationsPerMonth: -1,
      savedOpportunities: -1,
      projects: -1,
    },
  },
  agency: {
    name: 'Agency',
    price: 99,
    priceId: process.env.STRIPE_AGENCY_PRICE_ID,
    limits: {
      researchRunsPerMonth: -1,
      contentGenerationsPerMonth: -1,
      savedOpportunities: -1,
      projects: -1,
    },
  },
} as const;

export type PlanTier = keyof typeof PLANS;

export async function getUserSubscription(userId: string) {
  const sub = await prisma.subscription.findUnique({ where: { userId } });
  const tier = (sub?.tier ?? 'free') as PlanTier;
  return { subscription: sub, tier, plan: PLANS[tier] };
}

export async function getUserMonthlyUsage(userId: string) {
  const start = new Date();
  start.setDate(1);
  start.setHours(0, 0, 0, 0);

  const logs = await prisma.usageLog.groupBy({
    by: ['action'],
    where: { userId, date: { gte: start } },
    _count: true,
  });

  const usage: Record<string, number> = {};
  for (const log of logs) usage[log.action] = log._count;
  return {
    research_run: usage['research_run'] ?? 0,
    content_gen: usage['content_gen'] ?? 0,
    opportunity_save: usage['opportunity_save'] ?? 0,
  };
}

export async function checkUsageLimit(
  userId: string,
  action: 'research_run' | 'content_gen' | 'opportunity_save',
): Promise<{ allowed: boolean; reason?: string }> {
  const { plan } = await getUserSubscription(userId);
  const usage = await getUserMonthlyUsage(userId);

  const limitKey =
    action === 'research_run'
      ? 'researchRunsPerMonth'
      : action === 'content_gen'
      ? 'contentGenerationsPerMonth'
      : 'savedOpportunities';

  const limit = plan.limits[limitKey];
  if (limit === -1) return { allowed: true };

  const current = usage[action] ?? 0;
  if (current >= limit) {
    return {
      allowed: false,
      reason: `Monthly limit of ${limit} ${action.replace('_', ' ')}s reached. Upgrade to continue.`,
    };
  }
  return { allowed: true };
}

export async function trackUsage(
  userId: string,
  action: 'research_run' | 'content_gen' | 'opportunity_save',
) {
  await prisma.usageLog.create({ data: { userId, action } });
}

export async function createOrRetrieveCustomer(userId: string, email: string) {
  const existing = await prisma.subscription.findUnique({ where: { userId } });
  if (existing) return existing.stripeCustomerId;

  const customer = await stripe.customers.create({ email, metadata: { userId } });

  await prisma.subscription.create({
    data: {
      userId,
      stripeCustomerId: customer.id,
      tier: 'free',
      status: 'active',
    },
  });

  return customer.id;
}
