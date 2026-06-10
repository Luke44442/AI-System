"""AI shopping assistant.

Turns a natural-language request ("a summer fragrance under $150", "an outfit
for a car meet") into a structured product query, runs it, and returns curated
products plus a short stylist message.

Uses Claude to parse intent; falls back to keyword search if the LLM is
unavailable so the endpoint never hard-fails.
"""
from __future__ import annotations
import json
import logging
from decimal import Decimal

from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models.product import Product, Category

logger = logging.getLogger(__name__)

VALID_CATEGORIES = [
    "fragrances", "sneakers", "streetwear", "designer-clothing",
    "bags", "accessories", "watches", "jewelry",
]

_INTENT_PROMPT = """You are the AI shopping concierge for Aurevia, a luxury multi-category
marketplace (fragrances, sneakers, streetwear, designer clothing, bags, accessories,
watches, jewelry).

Parse the shopper's request into a JSON search intent. Return ONLY valid JSON:
{{
  "categories": ["zero or more of: {categories}"],
  "min_price": null,
  "max_price": null,
  "gender": null,
  "keywords": ["salient search terms — brands, colours, vibes, occasions"],
  "occasion": null,
  "stylist_message": "1-2 warm, concise sentences responding to the shopper and framing the picks"
}}

Rules:
- Only use category slugs from the allowed list. If unclear, leave categories empty.
- Infer price bounds from phrases like 'under $150' (max_price=150) or 'around $200'
  (min 150, max 250).
- gender is one of male|female|unisex or null.
- Keep stylist_message human and specific. Never mention JSON.

Shopper request: "{query}"
"""


def _extract_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}") + 1
    if start == -1 or end == 0:
        return {}
    try:
        return json.loads(text[start:end])
    except json.JSONDecodeError:
        return {}


async def parse_intent(query: str) -> dict:
    """Use Claude to parse a shopping request into structured intent."""
    if not settings.ANTHROPIC_API_KEY:
        return {"keywords": [query], "stylist_message": "Here are some pieces that match your search.", "categories": []}
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=settings.AI_MODEL,
            max_tokens=600,
            messages=[{"role": "user", "content": _INTENT_PROMPT.format(
                categories=", ".join(VALID_CATEGORIES), query=query)}],
        )
        intent = _extract_json(msg.content[0].text)
        return intent or {"keywords": [query], "categories": [], "stylist_message": "Here's what I found."}
    except Exception as exc:  # pragma: no cover
        logger.error("assistant parse_intent failed: %s", exc)
        return {"keywords": [query], "categories": [], "stylist_message": "Here's what I found."}


async def recommend(db: AsyncSession, query: str, limit: int = 12) -> dict:
    """Return {message, intent, products} for a natural-language shopping query."""
    intent = await parse_intent(query)

    stmt = select(Product).where(Product.is_active == True).options(selectinload(Product.brand))  # noqa: E712

    # Category filter
    categories = [c for c in (intent.get("categories") or []) if c in VALID_CATEGORIES]
    if categories:
        cat_ids = (await db.execute(select(Category.id).where(Category.slug.in_(categories)))).scalars().all()
        if cat_ids:
            stmt = stmt.where(Product.category_id.in_(cat_ids))

    # Price filter
    if intent.get("min_price") is not None:
        stmt = stmt.where(Product.website_price >= Decimal(str(intent["min_price"])))
    if intent.get("max_price") is not None:
        stmt = stmt.where(Product.website_price <= Decimal(str(intent["max_price"])))

    # Gender filter
    gender = intent.get("gender")
    if gender in ("male", "female", "unisex"):
        stmt = stmt.where(or_(Product.gender == gender, Product.gender == "unisex"))

    # Keyword full-text search
    keywords = [k for k in (intent.get("keywords") or []) if k]
    if keywords:
        term = " ".join(keywords)
        ts_query = func.websearch_to_tsquery("simple", term)
        stmt = stmt.where(or_(
            Product.search_vector.op("@@")(ts_query),
            Product.name.ilike(f"%{keywords[0]}%"),
        ))

    stmt = stmt.order_by(Product.is_featured.desc(), Product.order_count.desc()).limit(limit)
    products = list((await db.execute(stmt)).scalars().all())

    # Cold fallback: if filters were too narrow, relax to featured in-category.
    if not products and categories:
        cat_ids = (await db.execute(select(Category.id).where(Category.slug.in_(categories)))).scalars().all()
        fb = (select(Product).where(Product.is_active == True, Product.category_id.in_(cat_ids))  # noqa: E712
              .options(selectinload(Product.brand))
              .order_by(Product.is_featured.desc()).limit(limit))
        products = list((await db.execute(fb)).scalars().all())

    return {
        "message": intent.get("stylist_message") or "Here are some pieces I'd recommend.",
        "intent": {k: intent.get(k) for k in ("categories", "min_price", "max_price", "gender", "occasion")},
        "products": products,
    }
