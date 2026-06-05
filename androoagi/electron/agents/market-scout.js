'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Market Scout Agent
 * Discovers 15 ranked micro-business opportunities across Etsy, TikTok, digital products.
 */
async function runMarketScout({ emit, apiKey, focusNiche }) {
  const client = new Anthropic({ apiKey });

  emit('agent:status', {
    agent: 'scout',
    label: 'Market Scout',
    status: 'thinking',
    message: focusNiche ? `Scanning "${focusNiche}" niche...` : 'Scanning Etsy trends & digital product gaps...',
  });

  const nicheContext = focusNiche
    ? `Focus specifically on the "${focusNiche}" niche.`
    : 'Scan broadly across Etsy, TikTok trends, digital downloads, print-on-demand, and AI automation services.';

  const prompt = `You are a market research expert specializing in digital products and Etsy stores.
${nicheContext}

Find 15 profitable micro-business opportunities RIGHT NOW. For each, provide:
- id: sequential number 1-15
- title: short punchy name
- category: one of [digital_product, print_on_demand, etsy_physical, ai_service, template_pack]
- niche: specific niche name
- virality: score 1-10 (how viral/trending is this)
- monetization: score 1-10 (profit margin & revenue potential)
- competition: score 1-10 (10 = saturated, 1 = blue ocean)
- effort: score 1-10 (10 = very hard, 1 = quick to launch)
- price_range: e.g. "$7–$27"
- why_now: 1 sentence on WHY this is hot right now
- platform: primary platform (Etsy / TikTok Shop / Gumroad / Shopify)

Focus on:
✅ Digital downloads (highest margin)
✅ Low competition niches
✅ Evergreen demand (wedding, finance, productivity, business tools)
✅ AI-generated assets
✅ Templates over physical goods

Respond ONLY with valid JSON array. No markdown, no prose.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'scout', text: '🔍 Scanning markets...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-opus-4-8',
    max_tokens: 4000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'scout', text: chunk.delta.text });
    }
  }

  emit('agent:status', { agent: 'scout', status: 'parsing', message: 'Parsing opportunities...' });

  let opportunities = [];
  try {
    const match = fullText.match(/\[[\s\S]*\]/);
    if (match) {
      opportunities = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON array found in response');
    }
  } catch (err) {
    throw new Error(`Market Scout parse error: ${err.message}`);
  }

  // Compute overall score
  opportunities = opportunities.map(o => ({
    ...o,
    overall_score: Math.round(
      o.virality * 0.35 +
      o.monetization * 0.35 +
      (10 - o.competition) * 0.15 +
      (10 - o.effort) * 0.15
    ),
  })).sort((a, b) => b.overall_score - a.overall_score);

  emit('agent:complete', {
    agent: 'scout',
    label: 'Market Scout',
    summary: `Found ${opportunities.length} opportunities. Top pick: ${opportunities[0]?.title}`,
  });

  return opportunities;
}

module.exports = { runMarketScout };
