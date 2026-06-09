from __future__ import annotations
from typing import Optional
from app.models.product import Product


ETSY_TAXONOMY_ID = 2078  # Fragrances


def product_to_etsy_listing(product: Product, shop_id: str) -> dict:
    title = f"{product.brand.name + ' ' if product.brand else ''}{product.name}"
    if product.concentration:
        title += f" {product.concentration.title()}"
    if product.volume_ml:
        title += f" {product.volume_ml}ml"
    title = title[:140]

    tags = []
    if product.brand:
        tags.append(product.brand.name.lower()[:20])
    if product.fragrance_family:
        tags.append(product.fragrance_family.lower()[:20])
    if product.concentration:
        tags.append(product.concentration.lower()[:20])
    if product.gender != "unisex":
        tags.append(f"{product.gender}s perfume"[:20])
    tags.extend(["luxury perfume", "authentic fragrance", "designer perfume", "gift idea"])
    tags = list(dict.fromkeys(tags))[:13]

    description = product.description or product.short_description or title
    description += "\n\n✅ 100% Authentic\n🚚 Fast Shipping\n💎 Luxury Packaging"

    return {
        "title": title,
        "description": description[:2000],
        "price": {"amount": int(float(product.marketplace_price or 0) * 100), "divisor": 100, "currency_code": "USD"},
        "quantity": max(1, product.inventory_quantity),
        "tags": tags,
        "taxonomy_id": ETSY_TAXONOMY_ID,
        "who_made": "someone_else",
        "when_made": "made_to_order",
        "is_supply": False,
        "shipping_profile_id": None,
        "state": "draft",
        "materials": ["Glass", "Fragrance"],
    }
