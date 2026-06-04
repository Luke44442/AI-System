import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { stripe, PLANS, createOrRetrieveCustomer, type PlanTier } from '@/lib/stripe';

const Schema = z.object({
  tier: z.enum(['pro', 'creator_pro', 'agency']),
});

export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const body = await req.json();
    const { tier } = Schema.parse(body);

    const plan = PLANS[tier as PlanTier];
    if (!plan.priceId) {
      return NextResponse.json({ error: 'Plan not configured' }, { status: 400 });
    }

    const customerId = await createOrRetrieveCustomer(session.user.id, session.user.email!);

    const baseUrl = process.env.NEXTAUTH_URL ?? 'http://localhost:3000';

    const checkout = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: 'subscription',
      payment_method_types: ['card'],
      line_items: [{ price: plan.priceId, quantity: 1 }],
      success_url: `${baseUrl}/billing?success=true`,
      cancel_url: `${baseUrl}/billing?canceled=true`,
      metadata: { userId: session.user.id, tier },
      subscription_data: { metadata: { userId: session.user.id, tier } },
      allow_promotion_codes: true,
    });

    return NextResponse.json({ url: checkout.url });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    console.error('[stripe checkout]', err);
    return NextResponse.json({ error: 'Failed to create checkout session' }, { status: 500 });
  }
}
