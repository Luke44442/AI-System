'use strict';

/**
 * Execution Controller
 * Pure logic — no AI calls. Assembles the approval package.
 * NEVER publishes anything automatically. Always gates on human approval.
 */
function buildExecutionPackage({ opportunity, blueprint, listings, productSpec, growthPlan }) {
  const approvalItems = [
    {
      id: 'create_store',
      type: 'store_setup',
      label: 'Create Etsy Store',
      description: `Open "${blueprint.store_name}" on Etsy with the designed brand identity`,
      details: {
        store_name: blueprint.store_name,
        tagline: blueprint.tagline,
        bio: blueprint.store_bio,
        brand_colors: blueprint.brand_colors,
        seo_keywords: blueprint.seo_keywords,
      },
      status: 'pending',
      risk: 'low',
      platform: 'Etsy',
      estimated_time: '30–60 min',
    },
    {
      id: 'create_product',
      type: 'product_creation',
      label: 'Build Hero Product',
      description: `Create "${productSpec.product_title}" in Canva using the spec`,
      details: productSpec,
      status: 'pending',
      risk: 'low',
      platform: 'Canva',
      estimated_time: '2–4 hours',
    },
    {
      id: 'publish_listings',
      type: 'listing_publish',
      label: 'Publish Listings',
      description: `Publish ${listings.length} listings to Etsy store`,
      details: {
        listings: listings.map(l => ({ name: l.product_name, price: l.price })),
      },
      status: 'pending',
      risk: 'medium',
      platform: 'Etsy',
      estimated_time: '1–2 hours',
    },
    {
      id: 'launch_content',
      type: 'content_publish',
      label: 'Launch Social Content',
      description: 'Post Day 1 TikTok + Instagram Reels from growth plan',
      details: {
        tiktok_script: growthPlan.tiktok_scripts?.[0] ?? null,
        instagram: growthPlan.instagram_reels?.[0] ?? null,
      },
      status: 'pending',
      risk: 'low',
      platform: 'TikTok / Instagram',
      estimated_time: '1 hour',
    },
    {
      id: 'run_ads',
      type: 'paid_promotion',
      label: 'Enable Etsy Ads',
      description: `Start Etsy promoted listings at ${growthPlan.etsy_seo_plan?.promoted_listings_budget ?? '$2/day'}`,
      details: { budget: growthPlan.etsy_seo_plan?.promoted_listings_budget },
      status: 'pending',
      risk: 'high',
      platform: 'Etsy Ads',
      estimated_time: '15 min',
    },
  ];

  return {
    summary: `Full launch package for "${blueprint.store_name}"`,
    total_items: approvalItems.length,
    approvalItems,
    revenue_estimate: {
      day_7:  growthPlan.revenue_milestones?.day_7  ?? 'TBD',
      day_30: growthPlan.revenue_milestones?.day_30 ?? 'TBD',
      day_90: growthPlan.revenue_milestones?.day_90 ?? 'TBD',
    },
    readyForApproval: true,
    warning: 'REVIEW ALL ITEMS BEFORE APPROVING. Nothing has been published yet.',
  };
}

module.exports = { buildExecutionPackage };
