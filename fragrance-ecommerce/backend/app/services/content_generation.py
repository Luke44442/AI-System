"""Content generation service: TikTok scripts, SEO articles, email copy."""
from __future__ import annotations

import json
import logging
from typing import Any

log = logging.getLogger(__name__)

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


def _claude_client():
    if not _ANTHROPIC_AVAILABLE:
        raise RuntimeError("anthropic package not installed")
    return anthropic.Anthropic()


def _extract_json(text: str) -> dict:
    import re
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return {}


async def generate_tiktok_content(
    brand: str,
    name: str,
    concentration: str | None,
    fragrance_family: str | None,
    ai_description: str | None,
) -> dict[str, Any]:
    """Generate TikTok script, caption, and hashtags for a product."""
    client = _claude_client()

    product_line = f"{brand} {name}"
    if concentration:
        product_line += f" ({concentration})"

    prompt = f"""Generate TikTok content for this luxury fragrance: {product_line}
Fragrance family: {fragrance_family or 'unknown'}
Description: {ai_description or 'a premium fragrance'}

Return JSON with:
{{
  "hook": "attention-grabbing opening line (max 15 words)",
  "script": "full 30-second TikTok script (conversational, enthusiastic, 80-120 words)",
  "caption": "TikTok caption with emojis (max 150 chars)",
  "hashtags": ["list", "of", "10-15", "relevant", "hashtags"],
  "trending_audio_suggestions": ["2-3 trending song/audio suggestions that fit the vibe"],
  "target_age_range": "18-24 or 25-34 etc",
  "target_gender": "male/female/unisex"
}}"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


async def generate_content_item(
    content_type: str,
    brand: str | None = None,
    season: str | None = None,
    topic: str | None = None,
    product_ids: list[str] | None = None,
    brand_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate SEO blog content (guide, review, seasonal, etc.)."""
    client = _claude_client()

    if content_type == "seasonal_guide":
        subject = f"{season} fragrance guide"
    elif content_type == "brand_story" and brand:
        subject = f"{brand} brand story and fragrance history"
    elif content_type == "fragrance_guide":
        subject = topic or "fragrance buying guide"
    else:
        subject = topic or content_type

    prompt = f"""Write a luxury fragrance blog post about: {subject}

Return JSON with:
{{
  "title": "SEO-optimised article title",
  "slug": "url-friendly-slug",
  "excerpt": "1-2 sentence summary (max 160 chars)",
  "body": "full article body in Markdown (600-900 words, include H2 headings)",
  "seo_title": "meta title (max 60 chars)",
  "seo_description": "meta description (max 160 chars)",
  "seo_keywords": ["keyword1", "keyword2", "..."],
  "schema_markup": {{}}
}}"""

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )
    result = _extract_json(message.content[0].text)
    result["content_type"] = content_type
    result["brand_ids"] = brand_ids or []
    result["product_ids"] = product_ids or []
    return result
