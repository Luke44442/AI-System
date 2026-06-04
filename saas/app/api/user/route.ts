import { NextResponse } from 'next/server';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { getUserSubscription, getUserMonthlyUsage, PLANS } from '@/lib/stripe';

export async function GET() {
  try {
    const session = await requireAuth();
    const userId = session.user.id;

    const [{ subscription, tier, plan }, usage, workspace] = await Promise.all([
      getUserSubscription(userId),
      getUserMonthlyUsage(userId),
      prisma.workspace.findFirst({
        where: { userId },
        include: { _count: { select: { projects: true } } },
      }),
    ]);

    const limits = plan.limits;

    return NextResponse.json({
      user: { id: userId, name: session.user.name, email: session.user.email },
      subscription: {
        tier,
        status: subscription?.status ?? 'active',
        currentPeriodEnd: subscription?.currentPeriodEnd,
        cancelAtPeriodEnd: subscription?.cancelAtPeriodEnd ?? false,
        planName: plan.name,
        price: plan.price,
      },
      usage: {
        researchRuns: { used: usage.research_run, limit: limits.researchRunsPerMonth },
        contentGenerations: { used: usage.content_gen, limit: limits.contentGenerationsPerMonth },
        opportunitiesSaved: { used: usage.opportunity_save, limit: limits.savedOpportunities },
      },
      workspace: {
        id: workspace?.id,
        name: workspace?.name,
        projectCount: workspace?._count?.projects ?? 0,
        projectLimit: limits.projects,
      },
    });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch user data' }, { status: 500 });
  }
}
