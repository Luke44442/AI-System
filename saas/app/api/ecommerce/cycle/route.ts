import { NextResponse } from 'next/server';
import { z } from 'zod';
import { requireAuth } from '@/lib/auth';
import { prisma } from '@/lib/db';
import { checkUsageLimit, trackUsage } from '@/lib/stripe';
import { runMarketResearch } from '@/lib/ai/ecommerce/research';
import { validateOpportunities } from '@/lib/ai/ecommerce/validation';
import { buildStore } from '@/lib/ai/ecommerce/store-builder';
import { generateListings } from '@/lib/ai/ecommerce/listings';
import { generateProductSpecs } from '@/lib/ai/ecommerce/product-creation';
import { generateMarketingPlan } from '@/lib/ai/ecommerce/marketing';
import { buildExecutionPackage } from '@/lib/ai/ecommerce/execution-controller';

const Schema = z.object({
  focusNiche: z.string().max(200).optional(),
});

// Run the full 7-agent cycle (can take 2-4 minutes)
export async function POST(req: Request) {
  try {
    const session = await requireAuth();
    const userId = session.user.id;

    const body = await req.json().catch(() => ({}));
    const { focusNiche } = Schema.parse(body);

    // Check usage
    const limitCheck = await checkUsageLimit(userId, 'research_run');
    if (!limitCheck.allowed) {
      return NextResponse.json({ error: limitCheck.reason, upgradeRequired: true }, { status: 402 });
    }

    // Create cycle record
    const cycle = await prisma.ecommerceCycle.create({
      data: { userId, focusNiche: focusNiche ?? null, status: 'running' },
    });

    // Run the full pipeline asynchronously (don't await — return cycle ID immediately)
    void runCyclePipeline(userId, cycle.id, focusNiche).catch(async (err) => {
      console.error('[ecommerce cycle error]', err);
      await prisma.ecommerceCycle.update({
        where: { id: cycle.id },
        data: { status: 'error', errorMessage: (err as Error).message },
      });
    });

    await trackUsage(userId, 'research_run');

    return NextResponse.json({ cycleId: cycle.id, status: 'running' }, { status: 202 });
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    if (err instanceof z.ZodError) {
      return NextResponse.json({ error: err.errors[0].message }, { status: 400 });
    }
    console.error('[cycle POST]', err);
    return NextResponse.json({ error: 'Failed to start cycle' }, { status: 500 });
  }
}

// GET — poll cycle status
export async function GET(req: Request) {
  try {
    const session = await requireAuth();
    const { searchParams } = new URL(req.url);
    const cycleId = searchParams.get('cycleId');

    if (cycleId) {
      const cycle = await prisma.ecommerceCycle.findFirst({
        where: { id: cycleId, userId: session.user.id },
        include: {
          opportunities: { orderBy: { overallScore: 'desc' } },
          storeBlueprint: true,
          marketingPlan: true,
          approvalItems: { orderBy: { createdAt: 'asc' } },
        },
      });
      if (!cycle) return NextResponse.json({ error: 'Not found' }, { status: 404 });
      return NextResponse.json(cycle);
    }

    // List all cycles
    const cycles = await prisma.ecommerceCycle.findMany({
      where: { userId: session.user.id },
      orderBy: { createdAt: 'desc' },
      take: 20,
      select: {
        id: true, status: true, focusNiche: true, approvalStatus: true, createdAt: true,
        storeBlueprint: { select: { storeName: true } },
        _count: { select: { opportunities: true } },
      },
    });

    return NextResponse.json(cycles);
  } catch (err) {
    if ((err as Error).message === 'UNAUTHORIZED') {
      return NextResponse.json({ error: 'Unauthorized' }, { status: 401 });
    }
    return NextResponse.json({ error: 'Failed to fetch cycles' }, { status: 500 });
  }
}

// ── Pipeline ─────────────────────────────────────────────────────────────────

async function runCyclePipeline(userId: string, cycleId: string, focusNiche?: string) {
  console.log(`[cycle ${cycleId}] Starting pipeline`);

  // STEP 1: Market Research
  console.log(`[cycle ${cycleId}] Step 1: Market research`);
  const rawOpportunities = await runMarketResearch(focusNiche);

  await prisma.productOpportunity.createMany({
    data: rawOpportunities.map((o, i) => ({
      cycleId,
      rank: i + 1,
      name: o.name,
      description: o.description,
      category: o.category,
      productType: o.product_type,
      demandScore: o.demand_score,
      competitionLevel: o.competition_level,
      competitionScore: o.competition_score,
      monetizationScore: o.monetization_score,
      overallScore: o.overall_score,
      platforms: o.platforms,
      targetBuyer: o.target_buyer,
      priceRange: o.price_range,
      whyNow: o.why_now,
    })),
  });

  // STEP 2: Validation — narrow to top 3
  console.log(`[cycle ${cycleId}] Step 2: Validation`);
  const validated = await validateOpportunities(rawOpportunities);

  // Update opportunities with validation decisions
  for (const v of validated) {
    await prisma.productOpportunity.updateMany({
      where: { cycleId, name: v.name },
      data: {
        validationDecision: v.decision,
        validationReason: v.decision_reason,
        suggestedPrice: v.suggested_price,
        differentiators: v.differentiators ?? [],
        isTopPick: v === validated[0],
      },
    });
  }

  const topOpp = validated[0];
  const topOppRecord = await prisma.productOpportunity.findFirst({
    where: { cycleId, name: topOpp.name },
  });
  if (!topOppRecord) throw new Error('Top opportunity not found in DB');

  // STEP 3: Store Builder
  console.log(`[cycle ${cycleId}] Step 3: Store builder`);
  const storeBlueprint = await buildStore(topOpp);

  await prisma.storeBlueprint.create({
    data: {
      cycleId,
      storeName: storeBlueprint.store_name,
      storeNameAlts: storeBlueprint.store_name_alts ?? [],
      tagline: storeBlueprint.tagline,
      brandColors: storeBlueprint.brand_colors ?? [],
      brandTone: storeBlueprint.brand_tone,
      niche: storeBlueprint.niche,
      positioning: storeBlueprint.positioning,
      productCatalog: storeBlueprint.product_catalog as object[],
      launchChecklist: storeBlueprint.launch_checklist as object[],
    },
  });

  // STEP 4: Listings
  console.log(`[cycle ${cycleId}] Step 4: Listings`);
  const listings = await generateListings(topOpp, storeBlueprint, 5);

  for (const listing of listings) {
    await prisma.productListing.create({
      data: {
        opportunityId: topOppRecord.id,
        productName: listing.product_name,
        title: listing.title,
        description: listing.description,
        tags: listing.tags ?? [],
        keywords: listing.keywords ?? [],
        price: listing.price,
        bundleIdeas: listing.bundle_ideas ?? [],
        seoNotes: listing.seo_notes ?? [],
        designPrompts: [],
        fileSpecs: {},
      },
    });
  }

  // STEP 5: Product Specs
  console.log(`[cycle ${cycleId}] Step 5: Product specs`);
  const productSpec = await generateProductSpecs(topOpp, storeBlueprint);

  // Update the hero listing with design prompts
  const heroListing = await prisma.productListing.findFirst({ where: { opportunityId: topOppRecord.id } });
  if (heroListing) {
    await prisma.productListing.update({
      where: { id: heroListing.id },
      data: {
        designPrompts: productSpec.ai_generation_prompts ?? [],
        fileSpecs: productSpec as object,
      },
    });
  }

  // STEP 6: Marketing Plan
  console.log(`[cycle ${cycleId}] Step 6: Marketing plan`);
  const marketing = await generateMarketingPlan(topOpp, storeBlueprint);

  await prisma.marketingPlan.create({
    data: {
      cycleId,
      tiktokIdeas: marketing.tiktok_ideas as object[],
      instagramIdeas: marketing.instagram_ideas as object[],
      hookScripts: (marketing.hook_scripts as unknown) as string[],
      postingSchedule: marketing.posting_schedule as object[],
      launchStrategy: marketing.launch_strategy,
    },
  });

  // STEP 7: Execution Package (no AI needed)
  console.log(`[cycle ${cycleId}] Step 7: Execution controller`);
  const execPackage = buildExecutionPackage(topOpp, storeBlueprint, listings, productSpec, marketing);

  await prisma.approvalItem.createMany({
    data: execPackage.approval_items.map(item => ({
      cycleId,
      step: item.step,
      title: item.title,
      description: item.description,
      riskLevel: item.risk_level,
      instructions: item.instructions,
    })),
  });

  // Mark complete
  await prisma.ecommerceCycle.update({
    where: { id: cycleId },
    data: { status: 'complete', updatedAt: new Date() },
  });

  console.log(`[cycle ${cycleId}] Pipeline complete ✓`);
}
