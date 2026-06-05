'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Listing Engine
 * Generates 5 marketplace-ready Etsy listings for the top products.
 */
async function runListingEngine({ emit, apiKey, opportunity, blueprint }) {
  const client = new Anthropic({ apiKey });

  const topProducts = (blueprint.product_catalog ?? []).slice(0, 5);

  emit('agent:status', {
    agent: 'listing',
    label: 'Listing Engine',
    status: 'thinking',
    message: `Writing ${topProducts.length} SEO-optimized listings...`,
  });

  const prompt = `You are an expert Etsy SEO copywriter. Write marketplace-ready listings for these products.

Store: ${blueprint.store_name}
Niche: ${opportunity.niche}
Brand voice: ${blueprint.brand_voice}
Top SEO keywords: ${(blueprint.seo_keywords ?? []).join(', ')}

Products:
${JSON.stringify(topProducts, null, 2)}

For each product output:
- product_name: final listing title (max 140 chars, front-load keywords)
- price: number
- tags: array of exactly 13 Etsy tags (max 20 chars each)
- primary_image_prompt: detailed Midjourney/DALL-E prompt for the hero listing image
- description: full Etsy description (300–500 words, includes what's included, who it's for, how to use, FAQ)
- bundle_suggestion: one upsell/bundle idea

Respond ONLY with valid JSON array. No markdown.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'listing', text: '🧾 Writing Etsy listings...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 6000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'listing', text: chunk.delta.text });
    }
  }

  let listings = [];
  try {
    const match = fullText.match(/\[[\s\S]*\]/);
    if (match) {
      listings = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON array found');
    }
  } catch (err) {
    throw new Error(`Listing Engine parse error: ${err.message}`);
  }

  emit('agent:complete', {
    agent: 'listing',
    label: 'Listing Engine',
    summary: `${listings.length} listings ready. Top: "${listings[0]?.product_name}"`,
  });

  return listings;
}

module.exports = { runListingEngine };
