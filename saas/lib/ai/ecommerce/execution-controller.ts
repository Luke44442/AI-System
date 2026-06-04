import type { ValidatedOpportunity } from './validation';
import type { StoreBlueprint } from './store-builder';
import type { EtsyListing } from './listings';
import type { ProductSpec } from './product-creation';
import type { MarketingPlan } from './marketing';

export interface ApprovalItem {
  step: string;
  title: string;
  description: string;
  risk_level: 'low' | 'medium' | 'high';
  instructions: string;
  estimated_time: string;
  tools_needed: string[];
  cost_estimate: string;
}

export interface ExecutionPackage {
  summary: string;
  top_opportunity: string;
  store_name: string;
  estimated_monthly_revenue: string;
  total_startup_cost: string;
  time_to_launch_hours: number;
  approval_items: ApprovalItem[];
  risk_warnings: string[];
  success_metrics: string[];
  ready_for_approval: boolean;
}

export function buildExecutionPackage(
  topOpp: ValidatedOpportunity,
  store: StoreBlueprint,
  listings: EtsyListing[],
  productSpec: ProductSpec,
  marketing: MarketingPlan,
): ExecutionPackage {
  const approvalItems: ApprovalItem[] = [
    {
      step: 'create_product',
      title: `Create "${productSpec.product_name}"`,
      description: `Build the hero product using ${productSpec.software_needed}. This is the foundation of the store.`,
      risk_level: 'low',
      instructions: [
        `Tool: ${productSpec.software_needed}`,
        `Dimensions: ${productSpec.dimensions}`,
        `File formats to export: ${productSpec.file_formats?.join(', ')}`,
        `Design style: ${productSpec.design_style}`,
        `Time estimate: ${productSpec.creation_time_hours} hours`,
        '',
        'CREATION STEPS:',
        ...(productSpec.canva_instructions ?? []).map((step, i) => `${i + 1}. ${step}`),
        '',
        'QUALITY CHECKLIST:',
        ...(productSpec.quality_checklist ?? []).map(item => `☐ ${item}`),
      ].join('\n'),
      estimated_time: `${productSpec.creation_time_hours} hours`,
      tools_needed: [productSpec.software_needed, 'Canva (free)', 'Google Drive or Dropbox'],
      cost_estimate: '$0 (Canva free) or $12.99/month (Canva Pro)',
    },
    {
      step: 'setup_store',
      title: `Open Etsy Shop: ${store.store_name}`,
      description: 'Create and configure the Etsy storefront with branding, policies, and initial setup.',
      risk_level: 'low',
      instructions: [
        '1. Go to etsy.com → Sell on Etsy → Open your shop',
        `2. Shop name: "${store.store_name}"`,
        `   Alternatives: ${store.store_name_alts?.join(', ')}`,
        `3. Tagline: "${store.tagline}"`,
        '',
        'ABOUT SECTION:',
        store.about_section,
        '',
        'SHOP SECTIONS TO CREATE:',
        ...(store.etsy_shop_sections ?? []).map((s, i) => `${i + 1}. ${s}`),
        '',
        'BRAND COLORS:',
        store.brand_colors?.join(', '),
      ].join('\n'),
      estimated_time: '45 minutes',
      tools_needed: ['Etsy account (free)', 'Payment method for listing fees'],
      cost_estimate: '$0.20 per listing (Etsy fee)',
    },
    {
      step: 'create_listings',
      title: `Publish ${listings.length} Product Listings`,
      description: 'Copy-paste optimized listings with titles, descriptions, tags, and mockup images.',
      risk_level: 'low',
      instructions: listings.map((l, i) =>
        [
          `--- LISTING ${i + 1}: ${l.product_name} ---`,
          `TITLE: ${l.title}`,
          '',
          `PRICE: ${l.price}`,
          `QUANTITY: ${l.quantity}`,
          '',
          'DESCRIPTION:',
          l.description,
          '',
          `TAGS (copy all 13):`,
          l.tags?.join(', '),
          '',
          `BUNDLE IDEAS:`,
          ...(l.bundle_ideas ?? []).map(b => `• ${b}`),
          '',
          `PHOTOGRAPHY TIPS:`,
          ...(l.photography_tips ?? []).map(t => `• ${t}`),
        ].join('\n'),
      ).join('\n\n========================================\n\n'),
      estimated_time: `${listings.length * 20} minutes`,
      tools_needed: ['Etsy Seller dashboard', 'Canva (for mockups)', 'Placeit.net (mockup generator)'],
      cost_estimate: `$${(listings.length * 0.20).toFixed(2)} in Etsy listing fees`,
    },
    {
      step: 'create_content',
      title: 'Film First 3 TikTok Videos',
      description: 'Create organic content to drive traffic before spending on ads.',
      risk_level: 'low',
      instructions: [
        'LAUNCH CONTENT (do these FIRST — before publishing listings):',
        '',
        ...(marketing.tiktok_ideas?.slice(0, 3) ?? []).map((idea, i) =>
          [
            `--- VIDEO ${i + 1} ---`,
            `Format: ${idea.format}`,
            `HOOK (first 3 seconds): "${idea.hook}"`,
            `Concept: ${idea.concept}`,
            `Caption: ${idea.caption}`,
            `Hashtags: ${idea.hashtags?.join(' ')}`,
          ].join('\n'),
        ).join('\n\n'),
        '',
        'LAUNCH STRATEGY SUMMARY:',
        marketing.launch_strategy,
      ].join('\n'),
      estimated_time: '2-3 hours',
      tools_needed: ['TikTok app', 'iPhone/Android camera', 'CapCut (free editing)'],
      cost_estimate: '$0',
    },
    {
      step: 'run_ads',
      title: 'Start Etsy Ads ($5/day)',
      description: '⚠️ Only after first organic sale. Start ads on your best-performing listing.',
      risk_level: 'medium',
      instructions: [
        '⚠️ WAIT until you have at least 1 organic sale before starting ads.',
        '',
        marketing.etsy_ads_strategy,
        '',
        'FIRST 30 DAYS PLAN:',
        ...(marketing.first_30_days_plan ?? []).map(step => `${step}`),
      ].join('\n'),
      estimated_time: '15 minutes to set up',
      tools_needed: ['Etsy Seller dashboard', 'Credit/debit card for ad budget'],
      cost_estimate: '$5/day budget = $150/month max',
    },
  ];

  const totalHours = 2 + topOpp.startup_cost_usd / 50; // rough estimate

  return {
    summary: `Complete launch package for "${store.store_name}" — ${store.niche}. Top opportunity: ${topOpp.name}. Estimated ${topOpp.estimated_monthly_revenue}/month at full speed.`,
    top_opportunity: topOpp.name,
    store_name: store.store_name,
    estimated_monthly_revenue: topOpp.estimated_monthly_revenue,
    total_startup_cost: `$${topOpp.startup_cost_usd}–$${topOpp.startup_cost_usd + 50}`,
    time_to_launch_hours: Math.round(totalHours + productSpec.creation_time_hours + 2),
    approval_items: approvalItems,
    risk_warnings: [
      '⚠️ Never purchase ads before having organic proof of demand',
      '⚠️ Verify all designs are 100% original before publishing (no trademarked elements)',
      '⚠️ Read Etsy seller policies — some niches (e.g. NFTs) are prohibited',
      '⚠️ Keep startup costs under $50 until first 5 sales confirm demand',
      '⚠️ Do NOT pay for premium tools (Canva Pro, Placeit subscription) before first sale',
    ],
    success_metrics: [
      'Week 1: 100+ views on hero listing',
      'Week 2: First organic sale',
      'Month 1: 5+ sales, 3+ reviews',
      `Month 3: ${topOpp.estimated_monthly_revenue} monthly revenue run rate`,
      'Month 6: 50+ listings, 25+ reviews, $1000+/month',
    ],
    ready_for_approval: true,
  };
}
