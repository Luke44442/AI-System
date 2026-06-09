from __future__ import annotations
import json
from typing import Optional
import anthropic
from app.config import settings

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        return {}
    return json.loads(text[start:end])


def generate_product_listing(
    brand: str,
    product_name: str,
    concentration: Optional[str],
    volume_ml: Optional[int],
    gender: Optional[str],
    top_notes: Optional[list],
    middle_notes: Optional[list],
    base_notes: Optional[list],
    platform: str = "website",
    existing_description: Optional[str] = None,
) -> dict:
    notes_text = ""
    if top_notes:
        notes_text += f"Top notes: {', '.join(top_notes)}. "
    if middle_notes:
        notes_text += f"Middle notes: {', '.join(middle_notes)}. "
    if base_notes:
        notes_text += f"Base notes: {', '.join(base_notes)}."

    platform_instructions = {
        "website": "Write for a luxury fragrance e-commerce website. Use elegant, sensory language. Max 3 paragraphs.",
        "etsy": "Write for Etsy. Include searchable keywords naturally. Max 2000 chars. Mention authentic/genuine.",
        "ebay": "Write for eBay. Be factual and keyword-rich. Include size and concentration clearly.",
        "facebook": "Write for Facebook Marketplace. Conversational and friendly. Short and punchy.",
    }
    instruction = platform_instructions.get(platform, platform_instructions["website"])

    prompt = f"""You are a luxury fragrance copywriter. Generate a product listing for:

Brand: {brand}
Product: {product_name}
Concentration: {concentration or 'N/A'}
Size: {f'{volume_ml}ml' if volume_ml else 'N/A'}
Gender: {gender or 'unisex'}
{notes_text}
{f'Existing description to improve: {existing_description}' if existing_description else ''}

Platform instruction: {instruction}

Return ONLY valid JSON with these fields:
{{
  "title": "optimized SEO title under 70 chars",
  "description": "full product description",
  "short_description": "1-2 sentence summary",
  "seo_title": "SEO meta title under 60 chars",
  "seo_description": "SEO meta description under 160 chars",
  "tags": ["array", "of", "relevant", "tags"],
  "seo_keywords": ["keyword1", "keyword2"]
}}"""

    client = _get_client()
    message = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


def generate_collection_description(
    collection_name: str,
    theme: str,
    products: list[dict],
) -> dict:
    product_list = "\n".join([f"- {p.get('name', '')} by {p.get('brand', '')}" for p in products[:10]])
    prompt = f"""Generate marketing copy for a fragrance collection:

Collection: {collection_name}
Theme: {theme}
Featured products:
{product_list}

Return ONLY valid JSON:
{{
  "description": "compelling collection description (2 paragraphs)",
  "seo_title": "SEO title under 60 chars",
  "seo_description": "meta description under 160 chars"
}}"""

    client = _get_client()
    message = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=800,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)


def generate_social_content(
    product_name: str,
    brand: str,
    platform: str,
    price: Optional[float] = None,
    image_description: Optional[str] = None,
) -> dict:
    platform_map = {
        "tiktok": "TikTok (trending, casual, use emojis, include call-to-action, 150 chars max caption)",
        "instagram": "Instagram (aesthetic, aspirational, include 20-30 hashtags, 2200 chars max)",
        "pinterest": "Pinterest (inspirational, include SEO keywords in description, 500 chars)",
    }
    spec = platform_map.get(platform, "social media")

    prompt = f"""Create {spec} content for:
Product: {product_name} by {brand}
{f'Price: ${price}' if price else ''}
{f'Visual: {image_description}' if image_description else ''}

Return ONLY valid JSON:
{{
  "caption": "main post caption",
  "hashtags": ["hashtag1", "hashtag2"],
  "call_to_action": "CTA text"
}}"""

    client = _get_client()
    message = client.messages.create(
        model=settings.AI_MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    return _extract_json(message.content[0].text)
