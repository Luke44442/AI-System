import Anthropic from '@anthropic-ai/sdk';
import type { ValidatedOpportunity } from './validation';
import type { StoreBlueprint } from './store-builder';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ContentIdea {
  platform: string;
  format: string;
  hook: string;
  concept: string;
  caption: string;
  hashtags: string[];
  estimated_views: string;
}

export interface PostSchedule {
  day: string;
  time: string;
  platform: string;
  content_type: string;
  goal: string;
}

export interface MarketingPlan {
  tiktok_ideas: ContentIdea[];
  instagram_ideas: ContentIdea[];
  hook_scripts: string[];
  posting_schedule: PostSchedule[];
  launch_strategy: string;
  etsy_ads_strategy: string;
  pinterest_strategy: string;
  first_30_days_plan: string[];
}

const SYSTEM = `You are a viral content strategist and e-commerce marketing expert who has grown multiple Etsy shops to $10k+/month using organic social media.

You specialize in:
- TikTok hooks that stop the scroll (first 1-3 seconds are everything)
- Instagram Reels that showcase digital products without showing your face
- Pinterest SEO for evergreen product discovery
- Etsy Ads optimization for new shops with small budgets

You understand: the best Etsy marketing shows the TRANSFORMATION or RESULT, not just the product.`;

const USER_PROMPT = (opp: ValidatedOpportunity, store: StoreBlueprint) => `Create a complete marketing plan for this new Etsy store launch:

Store: ${store.store_name} — ${store.tagline}
Hero product: ${store.product_catalog.find(p => p.is_hero)?.name}
Niche: ${store.niche}
Target buyer: ${opp.buyer_persona}
Price: ${opp.suggested_price}

Return a JSON object:
{
  "tiktok_ideas": [
    {
      "platform": "TikTok",
      "format": "Tutorial | Day-in-life | Before/After | Reaction | POV | Storytime",
      "hook": "EXACT first 3 seconds of video (the line spoken or shown on screen)",
      "concept": "Full video concept (what happens in 30-60 seconds)",
      "caption": "Caption text with call to action",
      "hashtags": ["8-10 hashtags"],
      "estimated_views": "Realistic views for a new 0-follower account"
    }
    // 7 TikTok ideas
  ],
  "instagram_ideas": [
    // 5 Instagram Reel ideas, same format
  ],
  "hook_scripts": [
    // 10 standalone hook lines for TikTok/Reels that could apply to this niche
    // Format: "POV: [situation]" or "Stop scrolling if you [pain point]" etc.
  ],
  "posting_schedule": [
    {
      "day": "Monday",
      "time": "7pm EST",
      "platform": "TikTok",
      "content_type": "Tutorial",
      "goal": "Drive store traffic"
    }
    // 14-day posting schedule (2x/day for TikTok, 1x for Instagram)
  ],
  "launch_strategy": "Complete 500-word launch strategy covering: pre-launch prep, day 1 actions, week 1 momentum, and how to get first 5 reviews fast",
  "etsy_ads_strategy": "Specific Etsy Ads strategy for a $5/day budget — which listings to promote, when to start, how to optimize",
  "pinterest_strategy": "Pinterest SEO and pinning strategy for this niche (boards to create, pin frequency, keyword strategy)",
  "first_30_days_plan": [
    "Day 1: ...",
    "Day 3: ...",
    "Week 1: ...",
    "Week 2: ...",
    "Week 3: ...",
    "Day 30: ..."
  ]
}

Return ONLY the JSON object. No markdown.`;

export async function generateMarketingPlan(
  opp: ValidatedOpportunity,
  store: StoreBlueprint,
): Promise<MarketingPlan> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 8192,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(opp, store) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  return JSON.parse(cleaned) as MarketingPlan;
}
