import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ProductOpportunity {
  name: string;
  description: string;
  category: string;
  product_type: 'digital' | 'pod' | 'service' | 'physical';
  demand_score: number;        // 1-10
  competition_level: 'low' | 'medium' | 'high';
  competition_score: number;   // 1-10, lower = less competition = better
  monetization_score: number;  // 1-10
  overall_score: number;       // computed
  platforms: string[];
  target_buyer: string;
  price_range: string;
  why_now: string;
  keywords: string[];
}

const SYSTEM = `You are an expert e-commerce market researcher with 10 years of experience on Etsy, Shopify, and digital product marketplaces.

You specialize in finding:
- Low-competition niches with strong buyer demand
- Digital products (highest margin — templates, planners, bundles, presets, guides)
- Print-on-demand opportunities with viral potential
- "Boring but profitable" evergreen products that sell consistently

PRIORITY CRITERIA:
1. Digital products first (no inventory, instant delivery, 80-95% margin)
2. Print-on-demand (no upfront cost, automated fulfillment)
3. Simple service packages last (highest labor, lowest scale)

AVOID: Drop-shipping, trademarked brands, copyrighted content, oversaturated niches with 50k+ listings and no differentiation possible.

YOU MUST BE REALISTIC. Do not suggest ideas that are already dominated by 1000+ shops with thousands of reviews unless there's a clear differentiation angle.`;

const USER_PROMPT = (focusNiche?: string) => `Identify the top 15 product opportunities for an e-commerce seller to launch TODAY on Etsy and Shopify.

${focusNiche ? `Focus niche: "${focusNiche}"` : 'Scan across all niches — find the best opportunities right now.'}

Think about:
- What people are searching for but not finding good results
- Seasonal trends with low current supply
- Niches where top sellers are outdated, ugly, or overpriced
- Trending aesthetics that haven't saturated Etsy yet (check: cottagecore, dark academia, Y2K, clean girl, old money, coastal grandmother, etc.)
- Digital products that solve specific pain points: wedding planning, budget tracking, fitness, small business, teachers, nurses, real estate agents
- POD niches: pets, professions, hobbies, family milestones

For EACH opportunity return:
{
  "name": "Specific product/niche name (not generic)",
  "description": "What exactly the product is and why it sells (2-3 sentences)",
  "category": "Wedding | Planner | Template | Art | Fashion | Home | Pet | Hobby | Business | Health | Education",
  "product_type": "digital | pod | service | physical",
  "demand_score": <1-10, 10 = massive demand>,
  "competition_level": "low | medium | high",
  "competition_score": <1-10, LOWER = LESS competition = BETTER for seller>,
  "monetization_score": <1-10, considers price point + volume potential>,
  "platforms": ["Etsy", "Shopify", "Gumroad", etc.],
  "target_buyer": "Specific buyer description (e.g. 'Bride-to-be, 25-35, planning wedding in 6 months')",
  "price_range": "$X - $Y",
  "why_now": "One specific reason this is a good opportunity RIGHT NOW in 2025",
  "keywords": ["8-10 Etsy search keywords buyers actually use"]
}

Return ONLY a JSON array of exactly 15 objects. No markdown.`;

export async function runMarketResearch(focusNiche?: string): Promise<ProductOpportunity[]> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 8192,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(focusNiche) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '[]';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();

  const opps = JSON.parse(cleaned) as Omit<ProductOpportunity, 'overall_score'>[];

  return opps.map(o => ({
    ...o,
    overall_score: Math.round(
      o.demand_score * 0.35 +
      o.monetization_score * 0.35 +
      (10 - o.competition_score) * 1.5 +   // scale: max 15 points for low competition
      0,
    ) / 10 * 10, // normalize to 0-100
  })).map(o => ({
    ...o,
    overall_score: parseFloat((
      (o.demand_score / 10) * 35 +
      (o.monetization_score / 10) * 35 +
      ((10 - o.competition_score) / 10) * 30
    ).toFixed(1)),
  })).sort((a, b) => b.overall_score - a.overall_score);
}
