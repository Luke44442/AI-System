'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Product Creator Agent
 * Builds production-ready asset specs for the hero product.
 */
async function runProductCreator({ emit, apiKey, opportunity, blueprint, listings }) {
  const client = new Anthropic({ apiKey });

  const heroListing = listings[0];

  emit('agent:status', {
    agent: 'product',
    label: 'Product Creator',
    status: 'thinking',
    message: `Designing "${heroListing?.product_name}"...`,
  });

  const prompt = `You are a digital product creation expert specializing in Canva templates, PDF planners, and AI-generated assets.

Build a complete production spec for this product:
Store: ${blueprint.store_name}
Product: ${JSON.stringify(heroListing, null, 2)}
Opportunity: ${JSON.stringify(opportunity, null, 2)}

Output a JSON object with:
- product_title: final product name
- file_format: e.g. "PDF + Canva Template Link"
- page_count: number of pages/slides
- dimensions: e.g. "8.5x11 inches (US Letter)"
- color_palette: array of 4 hex colors
- font_pairing: { heading: "...", body: "..." }
- sections: array of sections/pages in the product, each with:
    - name: section name
    - purpose: what this section does for the buyer
    - content_elements: array of elements to include
- canva_template_structure: step-by-step instructions to build in Canva
- ai_image_prompts: array of 5 DALL-E/Midjourney prompts for product visuals
- mockup_instructions: how to create mockup images for Etsy
- included_files: list of files delivered to buyer
- delivery_method: how to deliver (Etsy digital download, etc.)
- bonus_ideas: 2-3 bonus items to add perceived value

Respond ONLY with valid JSON. No markdown.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'product', text: '🎨 Designing product assets...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-sonnet-4-6',
    max_tokens: 4000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'product', text: chunk.delta.text });
    }
  }

  let spec;
  try {
    const match = fullText.match(/\{[\s\S]*\}/);
    if (match) {
      spec = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON object found');
    }
  } catch (err) {
    throw new Error(`Product Creator parse error: ${err.message}`);
  }

  emit('agent:complete', {
    agent: 'product',
    label: 'Product Creator',
    summary: `"${spec.product_title}" spec complete — ${spec.page_count} pages, ${spec.included_files?.length ?? 0} files`,
  });

  return spec;
}

module.exports = { runProductCreator };
