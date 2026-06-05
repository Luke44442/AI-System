'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Growth Engine
 * Creates viral content strategy + 30-day launch plan.
 */
async function runGrowthEngine({ emit, apiKey, opportunity, blueprint, listings }) {
  const client = new Anthropic({ apiKey });

  emit('agent:status', {
    agent: 'growth',
    label: 'Growth Engine',
    status: 'thinking',
    message: 'Building viral growth strategy...',
  });

  const prompt = `You are a viral marketing expert and Etsy growth strategist.

Create a full go-to-market plan for:
Store: ${blueprint.store_name}
Hero product: ${listings[0]?.product_name}
Niche: ${opportunity.niche}
Target customer: ${blueprint.target_customer}

Output a JSON object with:
- tiktok_hooks: array of 7 opening hook lines for TikTok videos (make them scroll-stopping)
- tiktok_scripts: array of 3 full TikTok video scripts (15–30 seconds), each with:
    - hook: opening line
    - body: middle content
    - cta: call to action
    - hashtags: array of 10 hashtags
- instagram_reels: array of 5 Reels concepts with caption starters
- pinterest_strategy: array of 5 pin ideas with titles and descriptions
- etsy_seo_plan: {
    primary_keyword: string,
    long_tail_keywords: array of 8,
    listing_refresh_schedule: string,
    promoted_listings_budget: "$X/day recommendation"
  }
- email_sequences: array of 3 post-purchase emails (subject + body outline)
- launch_week_plan: array of 7 objects, each { day: number, platform: string, action: string, goal: string }
- month_2_strategy: 3-4 sentences on scaling after first 30 days
- revenue_milestones: { day_7: "$X", day_30: "$X", day_90: "$X" }

Make everything specific, actionable, and copy-paste ready.
Respond ONLY with valid JSON. No markdown.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'growth', text: '📈 Engineering growth strategy...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 5000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'growth', text: chunk.delta.text });
    }
  }

  let plan;
  try {
    const match = fullText.match(/\{[\s\S]*\}/);
    if (match) {
      plan = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON object found');
    }
  } catch (err) {
    throw new Error(`Growth Engine parse error: ${err.message}`);
  }

  emit('agent:complete', {
    agent: 'growth',
    label: 'Growth Engine',
    summary: `${plan.tiktok_scripts?.length ?? 0} TikTok scripts + 30-day launch plan ready`,
  });

  return plan;
}

module.exports = { runGrowthEngine };
