import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { generateContent, type ContentType } from '@/lib/ai/content';
import { checkUsageLimit, trackUsage } from '@/lib/stripe';

const VALID_TYPES: ContentType[] = [
  'tiktok_script',
  'youtube_idea',
  'instagram_caption',
  'ad_copy',
  'landing_page',
  'email_sequence',
  'twitter_thread',
];

const GenerateSchema = z.object({
  type: z.enum([
    'tiktok_script', 'youtube_idea', 'instagram_caption',
    'ad_copy', 'landing_page', 'email_sequence', 'twitter_thread',
  ]),
  topic: z.string().min(1).max(400),
  audience: z.string().max(200).optional(),
  projectId: z.string().optional(),
  save: z.boolean().default(false),
});

export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const userId = session.user.id;

    const body = await req.json();
    const { type, topic, audience, projectId, save } = GenerateSchema.parse(body);

    // Check usage limits
    const limitCheck = await checkUsageLimit(userId, 'content_gen');
    if (!limitCheck.allowed) {
      return NextResponse.json({ error: limitCheck.reason, upgradeRequired: true }, { status: 402 });
    }

    const result = await generateContent(type, topic, audience);

    // Track usage
    await trackUsage(userId, 'content_gen');

    // Optionally save to project
    if (save && projectId) {
      const project = await prisma.project.findFirst({
        where: { id: projectId, workspace: { userId } },
      });
      if (project) {
        await prisma.contentItem.create({
          data: {
            projectId,
            type,
            platform: result.platform,
            title: result.title,
            content: result.content,
            prompt: topic,
          },
        });
      }
    }

    return NextResponse.json(result);
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 });
    }
    console.error('[content POST]', err);
    return NextResponse.json({ error: 'Content generation failed. Please try again.' }, { status: 500 });
  }
}

export async function GET(req: Request) {
  try {
    const session = await requireAuth();
    const { searchParams } = new URL(req.url);
    const projectId = searchParams.get('projectId');
    const type = searchParams.get('type') as ContentType | null;

    const workspace = await prisma.workspace.findFirst({
      where: { userId: session.user.id },
    });
    if (!workspace) return NextResponse.json([]);

    const items = await prisma.contentItem.findMany({
      where: {
        ...(projectId ? { projectId } : { project: { workspaceId: workspace.id } }),
        ...(type ? { type } : {}),
      },
      orderBy: { createdAt: 'desc' },
      take: 50,
    });

    return NextResponse.json(items);
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch content' }, { status: 500 });
  }
}
