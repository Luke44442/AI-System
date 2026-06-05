'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Store Builder Agent
 * Creates a complete Etsy-style store blueprint for the hero opportunity.
 */
async function runStoreBuilder({ emit, apiKey, opportunity }) {
  const client = new Anthropic({ apiKey });

  emit('agent:status', {
    agent: 'store',
    label: 'Store Builder',
    status: 'thinking',
    message: `Building store for "${opportunity.title}"...`,
  });

  const prompt = `You are an expert Etsy store designer and brand strategist.

Build a complete store blueprint for this opportunity:
${JSON.stringify(opportunity, null, 2)}

Output a JSON object with:
- store_name: catchy, brandable name (not generic)
- tagline: short punchy tagline
- niche_positioning: 1-2 sentence market position
- brand_colors: { primary: "#hex", secondary: "#hex", accent: "#hex" }
- brand_voice: e.g. "friendly & professional", "bold & minimal"
- target_customer: who buys this (2-3 sentences)
- store_bio: Etsy about section (150 words max)
- seo_keywords: array of 10 high-volume Etsy search terms
- product_catalog: array of 12 products, each with:
    - name: product name
    - type: digital_download | template | printable | bundle
    - price: number (USD)
    - description: 1 sentence
    - upsell: optional upsell idea
- launch_checklist: array of 8 action items to open the store
- first_7_days_plan: array of 7 daily tasks for launch week

Respond ONLY with valid JSON. No markdown.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'store', text: '🏗️ Designing your store...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-opus-4-8',
    max_tokens: 5000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'store', text: chunk.delta.text });
    }
  }

  let blueprint;
  try {
    const match = fullText.match(/\{[\s\S]*\}/);
    if (match) {
      blueprint = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON object found');
    }
  } catch (err) {
    throw new Error(`Store Builder parse error: ${err.message}`);
  }

  emit('agent:complete', {
    agent: 'store',
    label: 'Store Builder',
    summary: `Store "${blueprint.store_name}" designed with ${blueprint.product_catalog?.length ?? 0} products`,
  });

  return blueprint;
}

module.exports = { runStoreBuilder };
