import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { runResearch } from '@/lib/ai/research';
import { checkUsageLimit, trackUsage } from '@/lib/stripe';

const Schema = z.object({
  topic: z.string().min(1).max(300),
  projectId: z.string().optional(),
});

export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const userId = session.user.id;

    const body = await req.json();
    const { topic, projectId } = Schema.parse(body);

    // Check usage limits
    const limitCheck = await checkUsageLimit(userId, 'research_run');
    if (!limitCheck.allowed) {
      return NextResponse.json({ error: limitCheck.reason, upgradeRequired: true }, { status: 402 });
    }

    // Run research
    const results = await runResearch(topic);

    // Persist run
    const run = await prisma.researchRun.create({
      data: {
        userId,
        projectId: projectId ?? null,
        topic,
        results: results as object[],
      },
    });

    // Track usage
    await trackUsage(userId, 'research_run');

    return NextResponse.json({ runId: run.id, topic, results });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 });
    }
    console.error('[research POST]', err);
    return NextResponse.json({ error: 'Research failed. Please try again.' }, { status: 500 });
  }
}

export async function GET(req: Request) {
  try {
    const session = await requireAuth();
    const { searchParams } = new URL(req.url);
    const limit = Math.min(parseInt(searchParams.get('limit') ?? '20'), 50);

    const runs = await prisma.researchRun.findMany({
      where: { userId: session.user.id },
      orderBy: { createdAt: 'desc' },
      take: limit,
      select: { id: true, topic: true, createdAt: true, projectId: true },
    });

    return NextResponse.json(runs);
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch runs' }, { status: 500 });
  }
}
