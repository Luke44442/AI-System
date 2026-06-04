import Anthropic from '@anthropic-ai/sdk';
import type { ValidatedOpportunity } from './validation';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface CatalogItem {
  name: string;
  type: string;
  price: string;
  description: string;
  is_hero: boolean;
}

export interface LaunchTask {
  order: number;
  task: string;
  time_estimate: string;
  platform: string;
}

export interface StoreBlueprint {
  store_name: string;
  store_name_alts: string[];
  tagline: string;
  brand_colors: string[];
  brand_tone: string;
  niche: string;
  positioning: string;
  about_section: string;
  product_catalog: CatalogItem[];
  launch_checklist: LaunchTask[];
  etsy_shop_sections: string[];
  first_week_goal: string;
}

const SYSTEM = `You are an expert Etsy shop designer and brand strategist who has helped launch 200+ successful stores.

You create cohesive, memorable store identities that convert browsers to buyers.
You understand Etsy algorithm: shops with 10+ listings rank better, niche clarity helps SEO, and brand consistency builds trust.

NAMING RULES:
- Avoid generic words like "Creative", "Digital", "Shop", "Studio" alone
- Best performing names: descriptive (TheCozyPlannerCo), playful (PaperMoonPrintables), or niche-specific (WeddingDayTemplates)
- Check: name should be unique, memorable, easy to spell, under 20 characters if possible`;

const USER_PROMPT = (opp: ValidatedOpportunity) => `Design a complete Etsy store for this winning opportunity:

Product: ${opp.name}
Type: ${opp.product_type}
Niche: ${opp.category}
Target buyer: ${opp.buyer_persona}
Price range: ${opp.suggested_price}
Differentiators: ${opp.differentiators?.join(', ')}

Return a single JSON object:
{
  "store_name": "Primary store name (memorable, searchable)",
  "store_name_alts": ["2 alternative name options"],
  "tagline": "One-line value proposition (under 100 chars)",
  "brand_colors": ["#hex1", "#hex2", "#hex3"],
  "brand_tone": "Tone description (e.g. 'warm and approachable', 'minimal and sophisticated')",
  "niche": "Exact niche description",
  "positioning": "2-3 sentences on how this store is different from competitors",
  "about_section": "Complete Etsy 'About' section text (150-200 words, personal, builds trust)",
  "product_catalog": [
    {
      "name": "Product name",
      "type": "digital | pod | bundle",
      "price": "$X",
      "description": "One-line description",
      "is_hero": true/false
    }
    // 10-15 products total — 1 hero, rest complementary
  ],
  "launch_checklist": [
    {
      "order": 1,
      "task": "Specific action item",
      "time_estimate": "X mins/hours",
      "platform": "Etsy | Canva | Notion | etc."
    }
    // 12-15 tasks to go from zero to live
  ],
  "etsy_shop_sections": ["Section 1 name", "Section 2 name", ...],
  "first_week_goal": "Specific, measurable goal for week 1 (e.g. '5 sales, 50 views/day')"
}

Return ONLY the JSON object. No markdown.`;

export async function buildStore(opp: ValidatedOpportunity): Promise<StoreBlueprint> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 6144,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(opp) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  return JSON.parse(cleaned) as StoreBlueprint;
}
