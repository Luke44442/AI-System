import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';

const Schema = z.object({
  itemId: z.string().optional(),
  cycleId: z.string().optional(),
  action: z.enum(['approve', 'reject', 'approve_all']),
});

export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const body = await req.json();
    const { itemId, cycleId, action } = Schema.parse(body);

    if (action === 'approve_all' && cycleId) {
      // Verify ownership
      const cycle = await prisma.ecommerceCycle.findFirst({
        where: { id: cycleId, userId: session.user.id },
      });
      if (!cycle) return NextResponse.json({ error: 'Not found' }, { status: 404 });

      await prisma.approvalItem.updateMany({
        where: { cycleId, status: 'pending' },
        data: { status: 'approved', approvedAt: new Date() },
      });

      await prisma.ecommerceCycle.update({
        where: { id: cycleId },
        data: { approvalStatus: 'approved' },
      });

      return NextResponse.json({ approved: true });
    }

    if (itemId) {
      // Verify ownership via cycle
      const item = await prisma.approvalItem.findFirst({
        where: { id: itemId, cycle: { userId: session.user.id } },
      });
      if (!item) return NextResponse.json({ error: 'Not found' }, { status: 404 });

      await prisma.approvalItem.update({
        where: { id: itemId },
        data: {
          status: action === 'approve' ? 'approved' : 'rejected',
          approvedAt: action === 'approve' ? new Date() : null,
        },
      });

      return NextResponse.json({ updated: true });
    }

    return NextResponse.json({ error: 'itemId or cycleId required' }, { status: 400 });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 });
    }
    return NextResponse.json({ error: 'Failed to update approval' }, { status: 500 });
  }
}
