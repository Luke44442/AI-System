import Anthropic from '@anthropic-ai/sdk';
import type { ValidatedOpportunity } from './validation';
import type { StoreBlueprint, CatalogItem } from './store-builder';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export interface EtsyListing {
  product_name: string;
  title: string;
  description: string;
  tags: string[];        // max 13 tags, each max 20 chars
  keywords: string[];    // long-tail search phrases
  price: string;
  quantity: number;
  bundle_ideas: string[];
  seo_notes: string[];
  photography_tips: string[];
}

const SYSTEM = `You are an Etsy SEO specialist and conversion copywriter with 8 years of experience optimizing marketplace listings.

ETSY TITLE RULES:
- Max 140 characters
- Lead with the PRIMARY keyword buyers search
- Include secondary keywords naturally
- Format: "[Primary keyword] | [Style/Feature] | [Use case] — [Store name]"
- Never keyword stuff — must read naturally

ETSY TAG RULES:
- Exactly 13 tags
- Each tag max 20 characters
- Mix: specific (3-4 word phrases), medium, broad
- Think like a buyer: what would they type?

DESCRIPTION RULES:
- First 160 chars are shown in search — make them count
- Structure: hook → what it is → what you get → why us → how to use → FAQ hint
- Include keywords naturally in first paragraph
- Use short paragraphs and bullet points
- End with urgency or CTA`;

const USER_PROMPT = (product: CatalogItem, opp: ValidatedOpportunity, store: StoreBlueprint) => `
Write a complete, optimized Etsy listing for:

Product: ${product.name}
Store: ${store.store_name} (${store.niche})
Target buyer: ${opp.buyer_persona}
Price: ${product.price}
Description hint: ${product.description}
Keywords to include: ${opp.keywords?.slice(0, 6).join(', ')}

Return a single JSON object:
{
  "product_name": "${product.name}",
  "title": "Optimized Etsy title (130-140 chars, starts with primary keyword)",
  "description": "Full listing description (400-600 words). Use \\n for line breaks. Include: hook, what you get (bullet list), why us, how to use, FAQ hint.",
  "tags": ["tag1", "tag2", ...exactly 13 tags, each max 20 chars],
  "keywords": ["5-8 long-tail search phrases buyers actually use"],
  "price": "${product.price}",
  "quantity": 999,
  "bundle_ideas": ["2-3 bundle or upsell ideas with specific pricing"],
  "seo_notes": ["3-4 specific tips to improve this listing's search rank over time"],
  "photography_tips": ["3-4 mock-up / thumbnail tips for this product type"]
}

Return ONLY the JSON object. No markdown.`;

export async function generateListings(
  opp: ValidatedOpportunity,
  store: StoreBlueprint,
  maxListings = 5,
): Promise<EtsyListing[]> {
  // Take the hero product + top N-1 catalog items
  const heroItems = store.product_catalog.filter(p => p.is_hero);
  const restItems = store.product_catalog.filter(p => !p.is_hero);
  const targets = [...heroItems, ...restItems].slice(0, maxListings);

  const listings: EtsyListing[] = [];

  for (const product of targets) {
    const msg = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 3000,
      system: SYSTEM,
      messages: [{ role: 'user', content: USER_PROMPT(product, opp, store) }],
    });

    const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
    const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
    try {
      listings.push(JSON.parse(cleaned) as EtsyListing);
    } catch {
      // Skip malformed listing, continue
    }
  }

  return listings;
}
