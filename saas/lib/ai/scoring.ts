import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ScoredOpportunity {
  title: string;
  overall_score: number;
  grade: 'A+' | 'A' | 'B' | 'C' | 'D';
  virality_score: number;
  monetization_score: number;
  competition_score: number;
  ease_score: number;
  time_to_revenue_weeks: number;
  estimated_monthly_revenue_usd: number;
  pros: string[];
  cons: string[];
  recommended_next_steps: string[];
  risk_factors: string[];
}

const SYSTEM = `You are a business analyst who evaluates content and business opportunities for creators and small businesses.

You provide honest, data-driven assessments based on real market conditions. You flag risks clearly.
You NEVER inflate scores or make unrealistic income projections.`;

const USER_PROMPT = (opportunity: string, context?: string) => `Score and analyze this opportunity:

Opportunity: "${opportunity}"
${context ? `Additional context: ${context}` : ''}

Return a single JSON object:
{
  "title": "Clean title for this opportunity",
  "overall_score": <0-100 weighted composite>,
  "grade": "A+" | "A" | "B" | "C" | "D",
  "virality_score": <0-100>,
  "monetization_score": <0-100>,
  "competition_score": <0-100, lower = less competition>,
  "ease_score": <0-100, higher = easier>,
  "time_to_revenue_weeks": <realistic weeks to first dollar>,
  "estimated_monthly_revenue_usd": <realistic 12-month monthly revenue for a solo creator, be conservative>,
  "pros": ["3-4 genuine advantages"],
  "cons": ["3-4 real challenges or risks"],
  "recommended_next_steps": ["3 concrete, specific first steps to pursue this"],
  "risk_factors": ["2-3 things that could make this fail"]
}

Scoring weights: virality 35%, monetization 35%, (100 - competition) 15%, ease 15%.
Be honest. A B score (65-75) is good. Reserve A+ for truly exceptional opportunities.

Return ONLY the raw JSON object. No markdown.`;

function gradeFromScore(score: number): ScoredOpportunity['grade'] {
  if (score >= 85) return 'A+';
  if (score >= 75) return 'A';
  if (score >= 65) return 'B';
  if (score >= 50) return 'C';
  return 'D';
}

export async function scoreOpportunity(
  opportunity: string,
  context?: string,
): Promise<ScoredOpportunity> {
  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 2048,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(opportunity, context) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const scored = JSON.parse(cleaned) as ScoredOpportunity;

  // Recompute overall + grade to ensure consistency
  scored.overall_score = Math.round(
    scored.virality_score * 0.35 +
      scored.monetization_score * 0.35 +
      (100 - scored.competition_score) * 0.15 +
      scored.ease_score * 0.15,
  );
  scored.grade = gradeFromScore(scored.overall_score);

  return scored;
}
