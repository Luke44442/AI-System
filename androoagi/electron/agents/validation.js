'use strict';

const Anthropic = require('@anthropic-ai/sdk');

/**
 * Validation Engine
 * Takes top opportunities and makes KEEP / TEST / DROP decisions.
 */
async function runValidation({ emit, apiKey, opportunities }) {
  const client = new Anthropic({ apiKey });

  const top5 = opportunities.slice(0, 5);

  emit('agent:status', {
    agent: 'validation',
    label: 'Validation Engine',
    status: 'thinking',
    message: `Validating top ${top5.length} opportunities...`,
  });

  const prompt = `You are a business validation expert. Analyze these ${top5.length} opportunities and decide which to LAUNCH, TEST, or DROP.

Opportunities:
${JSON.stringify(top5, null, 2)}

For each opportunity, output:
- id: same id as input
- title: same title
- decision: "launch" | "test" | "drop"
- confidence: 1-10
- revenue_estimate: monthly range e.g. "$200–$800/mo"
- time_to_first_sale: e.g. "3-7 days"
- top_risks: array of 2-3 short risk strings
- verdict: 1-2 sentence explanation of decision

Decision rules:
- LAUNCH: overall_score ≥ 7, low effort, clear demand signal
- TEST: mixed signals, worth a small experiment
- DROP: saturated, high effort, low margin, or trademarked

Respond ONLY with valid JSON array. No markdown.`;

  let fullText = '';

  emit('agent:chunk', { agent: 'validation', text: '🧪 Running validation analysis...\n\n' });

  const stream = await client.messages.stream({
    model: 'claude-opus-4-8',
    max_tokens: 3000,
    messages: [{ role: 'user', content: prompt }],
  });

  for await (const chunk of stream) {
    if (chunk.type === 'content_block_delta' && chunk.delta.type === 'text_delta') {
      fullText += chunk.delta.text;
      emit('agent:chunk', { agent: 'validation', text: chunk.delta.text });
    }
  }

  let validated = [];
  try {
    const match = fullText.match(/\[[\s\S]*\]/);
    if (match) {
      validated = JSON.parse(match[0]);
    } else {
      throw new Error('No JSON array found');
    }
  } catch (err) {
    throw new Error(`Validation parse error: ${err.message}`);
  }

  const launches = validated.filter(v => v.decision === 'launch');
  const hero = launches[0] ?? validated[0];

  emit('agent:complete', {
    agent: 'validation',
    label: 'Validation Engine',
    summary: `${launches.length} LAUNCH decisions. Building: ${hero?.title}`,
  });

  return { validated, hero };
}

module.exports = { runValidation };
