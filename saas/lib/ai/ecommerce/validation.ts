import Anthropic from '@anthropic-ai/sdk';
import type { ProductOpportunity } from './research';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ValidatedOpportunity extends ProductOpportunity {
  decision: 'launch' | 'test' | 'reject';
  decision_reason: string;
  suggested_price: string;
  estimated_monthly_revenue: string;
  time_to_first_sale_days: number;
  startup_cost_usd: number;
  differentiators: string[];
  competitor_weaknesses: string[];
  buyer_persona: string;
}

const SYSTEM = `You are a rigorous e-commerce business analyst who evaluates product ideas for real-world profitability.

You are skeptical, data-driven, and honest. You give "Launch" only to genuinely strong opportunities.
You consider: total addressable market, realistic pricing, actual competitor landscape, production complexity, and time investment.

Decision criteria:
- LAUNCH: High demand + low/medium competition + clear differentiation + achievable production + $20+/sale or high volume
- TEST: Good potential but uncertain demand or execution risk — needs a small pilot
- REJECT: Oversaturated, too complex, low margin, or unclear buyer intent`;

const USER_PROMPT = (opps: ProductOpportunity[]) => `Evaluate these ${opps.length} product opportunities. Narrow to the TOP 3 most profitable to pursue NOW.

Opportunities to evaluate:
${opps.slice(0, 8).map((o, i) => `${i + 1}. ${o.name} (${o.product_type}, demand: ${o.demand_score}/10, competition: ${o.competition_level}, price: ${o.price_range})`).join('\n')}

For each of the TOP 3 (the ones worth pursuing), return:
{
  "name": "exact name from input",
  "decision": "launch | test | reject",
  "decision_reason": "2-3 sentences explaining why",
  "suggested_price": "$X for individual / $Y for bundle",
  "estimated_monthly_revenue": "$X-Y/month (realistic for a new shop in month 3)",
  "time_to_first_sale_days": <number, realistic days to first sale>,
  "startup_cost_usd": <number, realistic cost to create and list>,
  "differentiators": ["3-4 specific ways to stand out from existing sellers"],
  "competitor_weaknesses": ["2-3 specific weaknesses in current top sellers"],
  "buyer_persona": "Detailed 2-3 sentence buyer description with demographics, pain points, and purchase trigger"
}

Return ONLY a JSON array of exactly 3 objects (your top 3 picks). No markdown.`;

export async function validateOpportunities(
  opps: ProductOpportunity[],
): Promise<ValidatedOpportunity[]> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 4096,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(opps) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '[]';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const validated = JSON.parse(cleaned) as Partial<ValidatedOpportunity>[];

  // Merge with full opportunity data
  return validated.map(v => {
    const original = opps.find(o => o.name === v.name) ?? opps[0];
    return { ...original, ...v } as ValidatedOpportunity;
  });
}
