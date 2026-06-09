from __future__ import annotations
from app.models.product import Product


def product_to_ebay_inventory_item(product: Product) -> dict:
    title = f"{product.brand.name + ' ' if product.brand else ''}{product.name}"
    if product.concentration:
        title += f" {product.concentration.title()}"
    if product.volume_ml:
        title += f" {product.volume_ml}ml"

    aspects = {}
    if product.brand:
        aspects["Brand"] = [product.brand.name]
    if product.concentration:
        aspects["Type"] = [product.concentration.title()]
    if product.volume_ml:
        aspects["Size"] = [f"{product.volume_ml} ml"]
    if product.gender:
        aspects["For"] = [product.gender.title()]
    if product.fragrance_family:
        aspects["Fragrance Family"] = [product.fragrance_family]
    if product.top_notes:
        aspects["Top Notes"] = [", ".join(product.top_notes[:3])]
    if product.base_notes:
        aspects["Base Notes"] = [", ".join(product.base_notes[:3])]

    images = [img["url"] for img in (product.images or []) if img.get("url")][:12]

    return {
        "product": {
            "title": title[:80],
            "description": product.description or product.short_description or title,
            "aspects": aspects,
            "imageUrls": images,
        },
        "condition": "NEW",
        "availability": {
            "shipToLocationAvailability": {
                "quantity": max(1, product.inventory_quantity)
            }
        },
    }


def product_to_ebay_offer(product: Product, inventory_item_group_key: str, marketplace_account_id: str) -> dict:
    price = float(product.marketplace_price or product.website_price or 0)
    return {
        "sku": product.sku,
        "marketplaceId": "EBAY_US",
        "format": "FIXED_PRICE",
        "availableQuantity": max(1, product.inventory_quantity),
        "categoryId": "180345",  # eBay category: Fragrances
        "listingDescription": product.description or product.name,
        "listingPolicies": {
            "fulfillmentPolicyId": marketplace_account_id,
            "paymentPolicyId": marketplace_account_id,
            "returnPolicyId": marketplace_account_id,
        },
        "pricingSummary": {
            "price": {"value": str(price), "currency": "USD"}
        },
        "merchantLocationKey": "default",
    }
