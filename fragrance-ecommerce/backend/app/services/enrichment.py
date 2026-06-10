from __future__ import annotations
import json
import logging
from typing import Optional
import anthropic
from app.config import settings

logger = logging.getLogger(__name__)

_client: Optional[anthropic.Anthropic] = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    return _client


def _extract_json(text: str) -> dict:
    """Extract the first JSON object found in an LLM response."""
    start = text.find("{")
    end = text.rfind("}") + 1
    if start == -1 or end == 0:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError as exc:
        logger.error("Failed to parse JSON from LLM response: %s", exc)
        return {}


async def enrich_product(
    brand: str,
    name: str,
    concentration: str,
    fragrance_family: str,
    gender: str,
) -> dict:
    """Use Claude to enrich a fragrance product with detailed metadata.

    Returns a dict containing notes, scores, descriptions, and recommendations.
    On error returns an empty dict so callers can store partial data gracefully.
    """
    prompt = f"""You are a master perfumer and luxury fragrance expert with encyclopaedic knowledge of fine perfumery.

Analyse this fragrance and return a richly detailed JSON object. Be accurate, not generic.

Fragrance details:
- Brand: {brand}
- Name: {name}
- Concentration: {concentration}
- Fragrance family: {fragrance_family}
- Gender positioning: {gender}

Return ONLY valid JSON — no prose, no markdown fences — with exactly these fields:
{{
  "top_notes": ["list of top note ingredients"],
  "middle_notes": ["list of heart/middle note ingredients"],
  "base_notes": ["list of base note ingredients"],
  "fragrance_family": "refined fragrance family classification",
  "longevity_score": 7.5,
  "projection_score": 6.0,
  "uniqueness_score": 8.0,
  "value_score": 7.0,
  "season_spring": 6.0,
  "season_summer": 4.0,
  "season_fall": 8.5,
  "season_winter": 9.0,
  "occasion_casual": 5.0,
  "occasion_formal": 8.0,
  "occasion_evening": 9.5,
  "occasion_office": 4.0,
  "occasion_outdoor": 3.0,
  "occasion_sport": 1.0,
  "similar_fragrances": [
    {{"name": "Fragrance Name", "brand": "Brand Name"}},
    {{"name": "Fragrance Name", "brand": "Brand Name"}},
    {{"name": "Fragrance Name", "brand": "Brand Name"}}
  ],
  "alternative_recommendations": [
    {{"name": "Fragrance Name", "brand": "Brand Name", "reason": "Why this is a good alternative"}},
    {{"name": "Fragrance Name", "brand": "Brand Name", "reason": "Why this is a good alternative"}}
  ],
  "ai_description": "2-3 sentences of elegant, evocative luxury copywriting that captures the essence of this fragrance. Use sensory language. No generic marketing fluff.",
  "ai_short_description": "1 sentence that captures the soul of this fragrance",
  "tiktok_hook": "The first 3 seconds of a TikTok video about this fragrance — must stop the scroll. Be bold, specific, intriguing."
}}

Scores are floats from 1.0 to 10.0. Be precise and differentiated — avoid clustering everything around 7."""

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _extract_json(message.content[0].text)
        if not result:
            logger.warning("enrich_product: empty result for %s %s", brand, name)
        return result
    except Exception as exc:
        logger.error("enrich_product failed for %s %s: %s", brand, name, exc)
        return {}


async def _enrich_with_prompt(prompt: str, max_tokens: int = 2000) -> dict:
    """Run an enrichment prompt through Claude and parse the JSON response."""
    try:
        client = _get_client()
        message = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return _extract_json(message.content[0].text)
    except Exception as exc:  # pragma: no cover - network/LLM failures
        logger.error("enrichment prompt failed: %s", exc)
        return {}


async def enrich_sneaker(brand: str, name: str, attributes: dict) -> dict:
    """Category-aware enrichment for sneakers."""
    prompt = f"""You are a sneaker expert and stylist with deep knowledge of sneaker culture, collabs, and resale.

Analyse this sneaker and return richly detailed JSON. Be accurate, not generic.

Sneaker:
- Brand: {brand}
- Name: {name}
- Known attributes: {json.dumps(attributes)}

Return ONLY valid JSON with exactly these fields:
{{
  "colorway": "official colorway name",
  "silhouette": "model/silhouette, e.g. Dunk Low, Air Jordan 4",
  "release_year": 2021,
  "material": "primary upper material",
  "style_tags": ["casual","streetwear","retro", "up to 6 style tags"],
  "outfit_pairings": [
    {{"title": "Outfit name", "items": ["item 1","item 2","item 3"], "occasion": "where to wear it"}},
    {{"title": "Outfit name", "items": ["item 1","item 2","item 3"], "occasion": "where to wear it"}}
  ],
  "complementary_categories": ["streetwear","accessories", "categories that pair well"],
  "hype_score": 8.0,
  "versatility_score": 7.0,
  "value_score": 8.5,
  "ai_description": "2-3 sentences of confident, culture-aware copywriting about this sneaker.",
  "ai_short_description": "1 punchy sentence.",
  "tiktok_hook": "Scroll-stopping first 3 seconds for a sneaker TikTok about this pair."
}}
Scores are floats 1.0-10.0. Be precise and differentiated."""
    return await _enrich_with_prompt(prompt)


async def enrich_apparel(brand: str, name: str, attributes: dict) -> dict:
    """Category-aware enrichment for streetwear / designer clothing."""
    prompt = f"""You are a fashion stylist and streetwear expert.

Analyse this garment and return richly detailed JSON. Be accurate, not generic.

Garment:
- Brand: {brand}
- Name: {name}
- Known attributes: {json.dumps(attributes)}

Return ONLY valid JSON with exactly these fields:
{{
  "garment_type": "Hoodie / T-Shirt / Jacket / etc",
  "fit": "Slim / Regular / Relaxed / Oversized",
  "material": "primary material",
  "season": "Spring / Summer / Fall / Winter / All-Season",
  "color": "primary colour",
  "style_tags": ["streetwear","minimal", "up to 6 tags"],
  "outfit_pairings": [
    {{"title": "Look name", "items": ["item 1","item 2","item 3"], "occasion": "where to wear it"}},
    {{"title": "Look name", "items": ["item 1","item 2","item 3"], "occasion": "where to wear it"}}
  ],
  "complementary_categories": ["sneakers","accessories"],
  "versatility_score": 7.0,
  "value_score": 8.0,
  "ai_description": "2-3 sentences of confident fashion copywriting.",
  "ai_short_description": "1 punchy sentence.",
  "tiktok_hook": "Scroll-stopping first 3 seconds for a fashion TikTok about this piece."
}}
Scores are floats 1.0-10.0."""
    return await _enrich_with_prompt(prompt)


async def enrich_bag(brand: str, name: str, attributes: dict) -> dict:
    """Category-aware enrichment for bags."""
    prompt = f"""You are a luxury accessories expert.

Analyse this bag and return richly detailed JSON.

Bag:
- Brand: {brand}
- Name: {name}
- Known attributes: {json.dumps(attributes)}

Return ONLY valid JSON with exactly these fields:
{{
  "bag_type": "Tote / Crossbody / Shoulder / Backpack / Clutch / Top Handle",
  "material": "primary material",
  "color": "primary colour",
  "dimensions": "approx W x H x D",
  "capacity": "what it fits, e.g. everyday essentials, laptop",
  "style_tags": ["luxury","everyday", "up to 6 tags"],
  "outfit_pairings": [
    {{"title": "Look name", "items": ["item 1","item 2"], "occasion": "where to carry it"}}
  ],
  "complementary_categories": ["accessories","fragrances"],
  "versatility_score": 8.0,
  "value_score": 7.5,
  "ai_description": "2-3 sentences of elegant luxury copywriting.",
  "ai_short_description": "1 elegant sentence.",
  "tiktok_hook": "Scroll-stopping first 3 seconds for a luxury bag TikTok."
}}
Scores are floats 1.0-10.0."""
    return await _enrich_with_prompt(prompt)


async def enrich_generic(category: str, brand: str, name: str, attributes: dict) -> dict:
    """Fallback enrichment for accessories, watches, jewelry, and new categories."""
    prompt = f"""You are a luxury retail expert specialising in {category}.

Analyse this product and return richly detailed JSON.

Product:
- Category: {category}
- Brand: {brand}
- Name: {name}
- Known attributes: {json.dumps(attributes)}

Return ONLY valid JSON with exactly these fields:
{{
  "style_tags": ["up to 6 descriptive tags"],
  "usage_recommendations": ["when/how to use or wear this"],
  "pairing_recommendations": [
    {{"category": "complementary category", "reason": "why it pairs well"}}
  ],
  "complementary_categories": ["categories that pair well"],
  "versatility_score": 7.0,
  "value_score": 7.5,
  "ai_description": "2-3 sentences of refined luxury copywriting.",
  "ai_short_description": "1 refined sentence.",
  "tiktok_hook": "Scroll-stopping first 3 seconds for a TikTok about this product."
}}
Scores are floats 1.0-10.0."""
    return await _enrich_with_prompt(prompt)


# Maps a category's attribute_schema_type to the right enrichment routine.
async def enrich_by_category(
    schema_type: str,
    brand: str,
    name: str,
    attributes: dict | None = None,
    *,
    concentration: str = "",
    fragrance_family: str = "",
    gender: str = "unisex",
) -> dict:
    """Dispatch enrichment to the category-appropriate generator.

    schema_type comes from Category.attribute_schema_type
    (fragrance|sneakers|clothing|bags|accessories|watches|jewelry).
    """
    attributes = attributes or {}
    if schema_type == "fragrance":
        return await enrich_product(brand, name, concentration, fragrance_family, gender)
    if schema_type == "sneakers":
        return await enrich_sneaker(brand, name, attributes)
    if schema_type == "clothing":
        return await enrich_apparel(brand, name, attributes)
    if schema_type == "bags":
        return await enrich_bag(brand, name, attributes)
    return await enrich_generic(schema_type or "luxury product", brand, name, attributes)


# Columns that ProductEnrichment accepts — used to filter LLM output safely.
_ENRICHMENT_FIELDS = {
    "top_notes", "middle_notes", "base_notes", "fragrance_family",
    "season_spring", "season_summer", "season_fall", "season_winter",
    "occasion_casual", "occasion_formal", "occasion_evening", "occasion_office",
    "occasion_outdoor", "occasion_sport",
    "longevity_score", "projection_score", "uniqueness_score", "value_score",
    "similar_fragrances", "alternative_recommendations",
    "ai_description", "ai_short_description", "tiktok_hook",
}
_LIST_FIELDS = {"top_notes", "middle_notes", "base_notes",
                "similar_fragrances", "alternative_recommendations"}


def _product_schema_type(product) -> str:
    """Derive the enrichment schema type from a Product ORM object."""
    pt = (getattr(product, "product_type", None) or "").lower()
    mapping = {"fragrance": "fragrance", "shoes": "sneakers", "sneakers": "sneakers",
               "clothing": "clothing", "accessories": "accessories", "bags": "bags",
               "watches": "watches", "jewelry": "jewelry"}
    if pt in mapping:
        return mapping[pt]
    # Fragrance signal: has a concentration.
    return "fragrance" if getattr(product, "concentration", None) else "accessories"


async def generate_product_enrichment(product) -> dict:
    """High-level entrypoint used by the enrichment router.

    Dispatches to the category-appropriate generator and returns a dict
    containing ONLY valid ProductEnrichment columns (plus ai_generated_at), so
    the result can be spread straight into the ORM model.
    """
    from datetime import datetime, timezone

    schema_type = _product_schema_type(product)
    brand = product.brand.name if getattr(product, "brand", None) else ""
    raw = await enrich_by_category(
        schema_type,
        brand,
        product.name,
        attributes=getattr(product, "attributes", None) or {},
        concentration=getattr(product, "concentration", "") or "",
        fragrance_family=getattr(product, "fragrance_family", "") or "",
        gender=getattr(product, "gender", "unisex") or "unisex",
    )

    # Non-fragrance enrichers return styling fields with no dedicated columns;
    # fold the useful bits into alternative_recommendations so nothing is lost.
    extras = []
    for key in ("outfit_pairings", "style_tags", "pairing_recommendations", "usage_recommendations"):
        if raw.get(key):
            extras.append({key: raw[key]})

    data = {k: v for k, v in raw.items() if k in _ENRICHMENT_FIELDS}
    for f in _LIST_FIELDS:
        data.setdefault(f, [])
    if extras and not data.get("alternative_recommendations"):
        data["alternative_recommendations"] = extras
    data["ai_generated_at"] = datetime.now(timezone.utc)
    return data


async def generate_tiktok_content(
    brand: str,
    name: str,
    concentration: str,
    fragrance_family: str,
    gender: str,
    price: float,
) -> dict:
    """Generate a complete TikTok/Instagram content package for a fragrance.

    Returns hook, script, caption, hashtags, audio suggestions, targeting info,
    and estimated views. On error returns an empty dict.
    """
    prompt = f"""You are a viral fragrance content creator who specialises in luxury fragrance TikTok content.
You have deep knowledge of trending sounds, Gen Z and Millennial fragrance culture, and what makes perfume content go viral.

Create a complete TikTok content package for:
- Brand: {brand}
- Fragrance: {name}
- Concentration: {concentration}
- Family: {fragrance_family}
- Gender: {gender}
- Price: ${price:.2f}

Return ONLY valid JSON with exactly these fields:
{{
  "hook": "The opening 3-second hook that stops the scroll. Must be bold and specific to THIS fragrance.",
  "script": "Full 30-60 second TikTok script with [VISUAL CUE] markers. Include product shots, scent description, price reveal, and CTA.",
  "caption": "Instagram/TikTok caption under 150 chars with emojis. Punchy and on-brand.",
  "hashtags": ["20 relevant hashtags without the # symbol — mix trending, niche, and brand-specific"],
  "trending_audio_suggestions": [
    "Song Name by Artist — why it fits this fragrance vibe",
    "Song Name by Artist — why it fits this fragrance vibe",
    "Song Name by Artist — why it fits this fragrance vibe"
  ],
  "target_age_range": "e.g. 18-34",
  "target_gender": "e.g. female / male / unisex",
  "estimated_views": 45000
}}

The script should feel authentic to TikTok — not corporate. Use fragrance community language (longevity, sillage, blind buy, etc.)."""

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=1800,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _extract_json(message.content[0].text)
        if not result:
            logger.warning("generate_tiktok_content: empty result for %s %s", brand, name)
        return result
    except Exception as exc:
        logger.error("generate_tiktok_content failed for %s %s: %s", brand, name, exc)
        return {}


async def generate_content_item(content_type: str, params: dict) -> dict:
    """Generate a full content item (blog post, brand page, collection, etc.) using Claude.

    content_type options: 'blog', 'brand_page', 'collection_page', 'gift_guide',
                          'comparison', 'seasonal'

    params should contain relevant context such as brand name, products list, theme,
    season, occasion, etc.

    Returns title, excerpt, body (full HTML), SEO fields, and schema_markup.
    On error returns an empty dict.
    """
    type_instructions: dict[str, str] = {
        "blog": (
            "Write an authoritative, engaging blog post for a luxury fragrance e-commerce site. "
            "Include an introduction, 3-5 informative sections with H2 headings, and a conclusion. "
            "Optimise naturally for SEO. Aim for 800-1200 words."
        ),
        "brand_page": (
            "Write a brand story page that celebrates the heritage, philosophy, and key fragrances of this brand. "
            "2-3 paragraphs plus a list of signature fragrances. Luxury, authoritative tone."
        ),
        "collection_page": (
            "Write compelling collection page copy. Lead with a mood/theme hook, describe the collection character, "
            "mention key products. 150-300 words of body copy plus a short excerpt."
        ),
        "gift_guide": (
            "Write a gift guide article. Include an intro, clearly headed sections for different recipient types or "
            "price tiers, and product recommendations with brief descriptions. Conversational but knowledgeable."
        ),
        "comparison": (
            "Write an honest, helpful comparison article between the specified fragrances. "
            "Cover notes, performance, occasions, value. Help the reader make a decision. 600-900 words."
        ),
        "seasonal": (
            "Write seasonal fragrance editorial content. Evoke the season vividly, tie scent choices to the mood "
            "and occasions of the season. Include product recommendations. 400-600 words."
        ),
    }

    instruction = type_instructions.get(
        content_type,
        "Write high-quality fragrance content for a luxury e-commerce website.",
    )

    params_text = "\n".join(f"- {k}: {v}" for k, v in params.items())

    schema_example: dict = {}
    if content_type == "blog":
        schema_example = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": "TITLE_HERE",
            "author": {"@type": "Organization", "name": "Aurevia"},
        }
    elif content_type == "brand_page":
        schema_example = {
            "@context": "https://schema.org",
            "@type": "Brand",
            "name": "BRAND_NAME_HERE",
        }

    prompt = f"""You are a senior content strategist and copywriter for Aurevia, a luxury fragrance e-commerce brand.

Content type: {content_type}
Task: {instruction}

Context parameters:
{params_text}

Return ONLY valid JSON with exactly these fields:
{{
  "title": "Compelling page/article title (max 70 chars for SEO)",
  "excerpt": "1-2 sentence excerpt or meta preview of the content",
  "body": "Full HTML body content. Use <h2>, <h3>, <p>, <ul>, <li>, <strong> tags appropriately. No <html>/<body>/<head> wrapper.",
  "seo_title": "SEO meta title under 60 chars — include primary keyword",
  "seo_description": "SEO meta description under 160 chars — compelling, includes CTA",
  "seo_keywords": ["primary keyword", "secondary keyword", "up to 8 relevant keywords total"],
  "schema_markup": {json.dumps(schema_example) if schema_example else "{}"}
}}

Write for a sophisticated audience who loves fragrance. Avoid clichés. Be specific, sensory, and authoritative."""

    try:
        client = _get_client()
        message = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}],
        )
        result = _extract_json(message.content[0].text)
        if not result:
            logger.warning("generate_content_item: empty result for type=%s", content_type)
        return result
    except Exception as exc:
        logger.error("generate_content_item failed for type=%s: %s", content_type, exc)
        return {}
