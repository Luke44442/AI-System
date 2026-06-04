import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({ apiKey: process.env.ANTHROPIC_API_KEY });

export type ContentType =
  | 'tiktok_script'
  | 'youtube_idea'
  | 'instagram_caption'
  | 'ad_copy'
  | 'landing_page'
  | 'email_sequence'
  | 'twitter_thread';

export interface GeneratedContent {
  type: ContentType;
  platform: string;
  title: string;
  content: string;
  hook?: string;
  cta?: string;
  hashtags?: string[];
  estimated_reach?: string;
}

const PLATFORM_MAP: Record<ContentType, string> = {
  tiktok_script: 'TikTok',
  youtube_idea: 'YouTube',
  instagram_caption: 'Instagram',
  ad_copy: 'Meta Ads',
  landing_page: 'Web',
  email_sequence: 'Email',
  twitter_thread: 'Twitter/X',
};

const PROMPTS: Record<ContentType, (topic: string, audience: string) => string> = {
  tiktok_script: (topic, audience) => `Write a viral TikTok script about: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Video title/concept",
  "hook": "First 3 seconds hook (the thing that stops the scroll)",
  "content": "Full script with timestamps:\\n[0:00] Hook\\n[0:03] ...\\n[0:30] CTA",
  "cta": "Clear call to action",
  "hashtags": ["8-10 relevant hashtags"],
  "estimated_reach": "Realistic reach estimate for a new creator"
}

Rules: 30-60 seconds script. Hook MUST be intriguing. Use pattern interrupt. End with clear CTA.
Return ONLY the JSON.`,

  youtube_idea: (topic, audience) => `Create a YouTube video concept about: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Click-worthy title (no clickbait, genuine value)",
  "hook": "Opening 30-second hook script",
  "content": "Full video outline with sections:\\n## Intro\\n## Point 1\\n## Point 2\\n## Point 3\\n## CTA",
  "cta": "End screen + description CTA",
  "hashtags": ["5-7 relevant tags"],
  "estimated_reach": "Views estimate for 1k-10k subscriber channel"
}

Rules: 8-15 minute format. Must have strong SEO title. Value-first structure.
Return ONLY the JSON.`,

  instagram_caption: (topic, audience) => `Write an Instagram caption about: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Post concept",
  "hook": "First line that appears before 'more' (makes them tap)",
  "content": "Full caption (150-300 words). Include line breaks for readability. Story → Value → CTA.",
  "cta": "Specific engagement CTA (question or action)",
  "hashtags": ["20-25 mix of large/medium/niche hashtags"],
  "estimated_reach": "Realistic reach estimate"
}

Return ONLY the JSON.`,

  ad_copy: (topic, audience) => `Write high-converting Facebook/Instagram ad copy for: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Ad campaign name",
  "hook": "Primary text opening (stops the scroll)",
  "content": "Full ad copy with:\\nPrimary Text (3 variations)\\nHeadline (3 variations)\\nDescription (2 variations)\\nCTA button options",
  "cta": "Best CTA button text",
  "hashtags": [],
  "estimated_reach": "Expected CTR range for cold audience"
}

Use proven frameworks: AIDA, PAS, or Before/After/Bridge. Be specific on pain points.
Return ONLY the JSON.`,

  landing_page: (topic, audience) => `Write a landing page for: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Page headline",
  "hook": "Hero section (headline + subheadline + hero CTA)",
  "content": "Full landing page copy:\\n# Hero\\n## Problem\\n## Solution\\n## Features (3)\\n## Social Proof\\n## FAQ (3 Q&A)\\n## Final CTA",
  "cta": "Primary CTA button text",
  "hashtags": [],
  "estimated_reach": "Expected conversion rate range"
}

Use proven copywriting: Clear value prop, address objections, social proof, urgency.
Return ONLY the JSON.`,

  email_sequence: (topic, audience) => `Write a 5-email welcome sequence for: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Sequence name",
  "hook": "Email 1 subject line (highest open rate)",
  "content": "All 5 emails:\\n## Email 1 (Day 0): Subject | Body\\n## Email 2 (Day 1): Subject | Body\\n## Email 3 (Day 3): Subject | Body\\n## Email 4 (Day 5): Subject | Body\\n## Email 5 (Day 7): Subject | Body",
  "cta": "Primary CTA across sequence",
  "hashtags": [],
  "estimated_reach": "Expected open rate + click rate"
}

Each email: 150-250 words. Story-driven. Build to the final offer naturally.
Return ONLY the JSON.`,

  twitter_thread: (topic, audience) => `Write a viral Twitter/X thread about: "${topic}"
Target audience: ${audience}

Format as JSON:
{
  "title": "Thread topic",
  "hook": "Tweet 1 - the hook tweet (makes them want to read the thread)",
  "content": "Full thread:\\nTweet 1 (Hook):\\nTweet 2:\\nTweet 3:\\n...\\nTweet 10 (CTA):",
  "cta": "Final tweet CTA",
  "hashtags": ["3-5 hashtags for the hook tweet"],
  "estimated_reach": "Expected impressions for 1k-5k followers"
}

Rules: 8-12 tweets. Each tweet max 280 chars. Value bomb in every tweet. Strong hook.
Return ONLY the JSON.`,
};

const SYSTEM = `You are an expert content strategist and copywriter who creates high-performing content for creators and businesses.

You write content that is:
- Genuine and valuable (not clickbait)
- Platform-optimized (you know what works on each platform)
- Conversion-focused with clear CTAs
- Ethical and honest (no false claims, no deceptive tactics)

You produce ready-to-use content that creators can publish or customize.`;

export async function generateContent(
  type: ContentType,
  topic: string,
  audience: string = 'general audience',
): Promise<GeneratedContent> {
  const promptFn = PROMPTS[type];
  const prompt = promptFn(topic, audience);

  const msg = await client.messages.create({
    model: 'claude-opus-4-8',
    max_tokens: 4096,
    system: SYSTEM,
    messages: [{ role: 'user', content: prompt }],
  });

  const raw = msg.content[0].type === 'text' ? msg.content[0].text : '{}';
  const cleaned = raw.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const parsed = JSON.parse(cleaned);

  return {
    type,
    platform: PLATFORM_MAP[type],
    title: parsed.title,
    content: parsed.content,
    hook: parsed.hook,
    cta: parsed.cta,
    hashtags: parsed.hashtags ?? [],
    estimated_reach: parsed.estimated_reach,
  };
}
