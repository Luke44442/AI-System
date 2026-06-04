import { getAuthSession } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { getUserSubscription, getUserMonthlyUsage } from '@/lib/stripe';
import { UsageCard } from '@/components/dashboard/UsageCard';
import { QuickResearch } from '@/components/dashboard/QuickResearch';
import { RecentRuns } from '@/components/dashboard/RecentRuns';
import { Zap, Target, FileText, TrendingUp } from 'lucide-react';

export default async function DashboardPage() {
  const session = await getAuthSession();
  const userId = session!.user.id;

  const [{ tier, plan }, usage, recentRuns, savedOpps, contentCount] = await Promise.all([
    getUserSubscription(userId),
    getUserMonthlyUsage(userId),
    prisma.researchRun.findMany({
      where: { userId },
      orderBy: { createdAt: 'desc' },
      take: 5,
      select: { id: true, topic: true, createdAt: true },
    }),
    prisma.savedOpportunity.count({ where: { project: { workspace: { userId } } } }),
    prisma.contentItem.count({ where: { project: { workspace: { userId } } } }),
  ]);

  const limits = plan.limits;

  const STATS = [
    {
      label: 'Research Runs',
      value: usage.research_run,
      limit: limits.researchRunsPerMonth,
      icon: <TrendingUp size={16} />,
      color: 'violet',
    },
    {
      label: 'Content Generated',
      value: usage.content_gen,
      limit: limits.contentGenerationsPerMonth,
      icon: <Zap size={16} />,
      color: 'sky',
    },
    {
      label: 'Opportunities Saved',
      value: savedOpps,
      limit: limits.savedOpportunities,
      icon: <Target size={16} />,
      color: 'emerald',
    },
    {
      label: 'Content Library',
      value: contentCount,
      limit: null,
      icon: <FileText size={16} />,
      color: 'amber',
    },
  ];

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Good day, {session?.user?.name?.split(' ')[0] ?? 'there'} 👋
        </h1>
        <p className="text-slate-400 text-sm mt-1">
          You&apos;re on the <span className="text-violet-400 font-medium">{plan.name}</span> plan.{' '}
          {tier === 'free' && (
            <a href="/billing" className="text-violet-400 hover:underline">Upgrade for more →</a>
          )}
        </p>
      </div>

      {/* Usage stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {STATS.map(s => (
          <UsageCard key={s.label} {...s} />
        ))}
      </div>

      {/* Quick research + recent runs */}
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        <QuickResearch />
        <RecentRuns runs={recentRuns} />
      </div>
    </div>
  );
}
