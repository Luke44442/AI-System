import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ResearchOpportunity {
  title: string;
  description: string;
  niche: string;
  platforms: string[];
  virality_score: number;
  monetization_score: number;
  competition_score: number;
  ease_score: number;
  overall_score: number;
  keywords: string[];
  content_angle: string;
  why_now: string;
}

const SYSTEM = `You are a market research expert who identifies trending content opportunities and profitable niches for creators and small businesses.

You specialize in finding:
- Viral content opportunities with strong engagement potential
- Underserved niches with clear monetization paths
- Platform-specific trends before they peak
- Content gaps that competitors have missed

You focus ONLY on legal, ethical, sustainable opportunities: content creation, education, SaaS tools, digital products, services, and community building.

You NEVER suggest spam, deception, MLM schemes, unrealistic income claims, or anything unethical.`;

const USER_PROMPT = (topic: string) => `Analyze this topic and identify the top 10 content and business opportunities right now:

Topic: "${topic}"

Return a JSON array with exactly 10 opportunities. Each must have these exact fields:
{
  "title": "Specific, compelling opportunity title (not generic)",
  "description": "2-3 sentences explaining the opportunity and who it's for",
  "niche": "Specific sub-niche (e.g. 'AI productivity for solopreneurs', not just 'AI')",
  "platforms": ["Top 2-3 platforms where this performs best"],
  "virality_score": <0-100, how trending/viral this is RIGHT NOW>,
  "monetization_score": <0-100, revenue potential over 12 months>,
  "competition_score": <0-100, LOWER means LESS competition (better)>,
  "ease_score": <0-100, HIGHER means easier to start>,
  "keywords": ["5-7 specific keywords/hashtags"],
  "content_angle": "The unique hook or angle that makes this stand out",
  "why_now": "One specific reason this opportunity is timely in 2025"
}

Be specific and actionable. Avoid generic advice. Think like a creator who needs to start TODAY.

Return ONLY the raw JSON array. No markdown, no explanation.`;

export async function runResearch(topic: string): Promise<ResearchOpportunity[]> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 4096,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(topic) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '[]';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();

  const opps = JSON.parse(cleaned) as Omit<ResearchOpportunity, 'overall_score'>[];

  return opps
    .map((o) => ({
      ...o,
      overall_score: Math.round(
        o.virality_score * 0.35 +
          o.monetization_score * 0.35 +
          (100 - o.competition_score) * 0.15 +
          o.ease_score * 0.15,
      ),
    }))
    .sort((a, b) => b.overall_score - a.overall_score);
}
