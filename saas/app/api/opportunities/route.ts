import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { scoreOpportunity } from '@/lib/ai/scoring';
import { checkUsageLimit, trackUsage } from '@/lib/stripe';

const SaveSchema = z.object({
  projectId: z.string(),
  title: z.string().min(1),
  description: z.string(),
  niche: z.string(),
  platforms: z.array(z.string()),
  overallScore: z.number(),
  viralityScore: z.number(),
  monetizationScore: z.number(),
  competitionScore: z.number(),
  easeScore: z.number(),
  contentAngle: z.string().optional(),
  whyNow: z.string().optional(),
  keywords: z.array(z.string()),
});

const ScoreSchema = z.object({
  opportunity: z.string().min(1).max(500),
  context: z.string().max(500).optional(),
});

export async function GET(req: Request) {
  try {
    const session = await requireAuth();
    const { searchParams } = new URL(req.url);
    const projectId = searchParams.get('projectId');

    const workspace = await prisma.workspace.findFirst({
      where: { userId: session.user.id },
    });
    if (!workspace) return NextResponse.json([]);

    const where = projectId
      ? { projectId, project: { workspaceId: workspace.id } }
      : { project: { workspaceId: workspace.id } };

    const opps = await prisma.savedOpportunity.findMany({
      where,
      orderBy: { overallScore: 'desc' },
      take: 100,
    });

    return NextResponse.json(opps);
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch opportunities' }, { status: 500 });
  }
}

export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const body = await req.json();

    // Check if this is a save or a score request
    if (body.action === 'score') {
      const { opportunity, context } = ScoreSchema.parse(body);
      const result = await scoreOpportunity(opportunity, context);
      return NextResponse.json(result);
    }

    // Save opportunity
    const limitCheck = await checkUsageLimit(session.user.id, 'opportunity_save');
    if (!limitCheck.allowed) {
      return NextResponse.json({ error: limitCheck.reason, upgradeRequired: true }, { status: 402 });
    }

    const data = SaveSchema.parse(body);

    // Verify project belongs to user
    const project = await prisma.project.findFirst({
      where: {
        id: data.projectId,
        workspace: { userId: session.user.id },
      },
    });
    if (!project) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 });
    }

    const opp = await prisma.savedOpportunity.create({
      data: {
        projectId: data.projectId,
        title: data.title,
        description: data.description,
        niche: data.niche,
        platforms: data.platforms,
        overallScore: data.overallScore,
        viralityScore: data.viralityScore,
        monetizationScore: data.monetizationScore,
        competitionScore: data.competitionScore,
        easeScore: data.easeScore,
        contentAngle: data.contentAngle,
        whyNow: data.whyNow,
        keywords: data.keywords,
      },
    });

    await trackUsage(session.user.id, 'opportunity_save');
    return NextResponse.json(opp, { status: 201 });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 });
    }
    console.error('[opportunities POST]', err);
    return NextResponse.json({ error: 'Failed to process opportunity' }, { status: 500 });
  }
}

export async function DELETE(req: Request) {
  try {
    const session = await requireAuth();
    const { searchParams } = new URL(req.url);
    const id = searchParams.get('id');
    if (!id) return NextResponse.json({ error: 'ID required' }, { status: 400 });

    // Verify ownership
    const opp = await prisma.savedOpportunity.findFirst({
      where: { id, project: { workspace: { userId: session.user.id } } },
    });
    if (!opp) return NextResponse.json({ error: 'Not found' }, { status: 404 });

    await prisma.savedOpportunity.delete({ where: { id } });
    return NextResponse.json({ deleted: true });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to delete' }, { status: 500 });
  }
}
