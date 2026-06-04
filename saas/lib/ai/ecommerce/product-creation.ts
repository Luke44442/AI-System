import Anthropic from '@anthropic-ai/sdk';
import type { ValidatedOpportunity } from './validation';
import type { StoreBlueprint } from './store-builder';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface ProductSpec {
  product_name: string;
  product_type: string;
  file_formats: string[];
  dimensions: string;
  page_count_or_size: string;
  software_needed: string;
  creation_time_hours: number;
  ai_generation_prompts: string[];
  canva_instructions: string[];
  design_style: string;
  color_palette: string[];
  must_include_elements: string[];
  quality_checklist: string[];
  mockup_instructions: string;
  outsource_options: string[];
}

const SYSTEM = `You are a digital product creation expert who specializes in Etsy-ready digital downloads, Canva templates, and print-on-demand designs.

You provide precise, actionable creation instructions that someone with basic Canva skills can follow.
You also provide AI image generation prompts for Midjourney/DALL-E when relevant.

QUALITY STANDARDS:
- Digital downloads: 300 DPI for printables, proper bleed for POD
- Canva templates: must be fully editable, use free Canva fonts only (unless specifying Canva Pro)
- PDF Planners: A4 and US Letter both, hyperlinked navigation for digital versions
- POD: 4500x5400px minimum for Printful/Printify shirts`;

const USER_PROMPT = (opp: ValidatedOpportunity, store: StoreBlueprint) => `Create detailed product specifications for the HERO product in this store:

Store: ${store.store_name}
Hero product: ${store.product_catalog.find(p => p.is_hero)?.name ?? store.product_catalog[0]?.name}
Product type: ${opp.product_type}
Niche: ${opp.category}
Target buyer: ${opp.buyer_persona}
Design tone: ${store.brand_tone}
Brand colors: ${store.brand_colors?.join(', ')}

Return a JSON object:
{
  "product_name": "Hero product name",
  "product_type": "${opp.product_type}",
  "file_formats": ["PDF", "PNG", etc. — all formats to deliver],
  "dimensions": "Exact dimensions (e.g. '8.5 x 11 inches / A4')",
  "page_count_or_size": "Number of pages or file size",
  "software_needed": "Primary tool to create (Canva, Procreate, Illustrator, etc.)",
  "creation_time_hours": <realistic hours for a beginner>,
  "ai_generation_prompts": [
    "3-5 specific Midjourney or DALL-E prompts for generating design elements if needed"
  ],
  "canva_instructions": [
    "Step-by-step Canva creation instructions (8-12 steps)"
  ],
  "design_style": "Visual style description",
  "color_palette": ["#hex1", "#hex2", "#hex3", "#hex4"],
  "must_include_elements": ["List of required design elements for this product"],
  "quality_checklist": ["8-10 quality check items before publishing"],
  "mockup_instructions": "How to create a compelling product mockup for the listing thumbnail",
  "outsource_options": ["2-3 options to outsource creation (Fiverr, Creative Market, etc.) with cost estimate"]
}

Return ONLY the JSON object. No markdown.`;

export async function generateProductSpecs(
  opp: ValidatedOpportunity,
  store: StoreBlueprint,
): Promise<ProductSpec> {
  const msg = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    system: SYSTEM,
    messages: [{ role: 'user', content: USER_PROMPT(opp, store) }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  return JSON.parse(cleaned) as ProductSpec;
}
