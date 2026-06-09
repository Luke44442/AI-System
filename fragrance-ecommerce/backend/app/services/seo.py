from __future__ import annotations
import re
from typing import Optional
import unicodedata


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text.lower())
    text = re.sub(r"[-\s]+", "-", text).strip("-")
    return text


def generate_product_slug(brand: str, name: str, volume_ml: Optional[int] = None, concentration: Optional[str] = None) -> str:
    parts = [brand, name]
    if concentration:
        parts.append(concentration)
    if volume_ml:
        parts.append(f"{volume_ml}ml")
    return slugify("-".join(parts))


def generate_seo_title(brand: str, name: str, concentration: Optional[str] = None, volume_ml: Optional[int] = None) -> str:
    parts = [brand, name]
    if concentration:
        parts.append(concentration)
    if volume_ml:
        parts.append(f"{volume_ml}ml")
    title = " ".join(parts)
    if len(title) > 55:
        title = f"{brand} {name}"[:55]
    return f"{title} | Scentara"[:70]


def generate_seo_description(
    brand: str,
    name: str,
    concentration: Optional[str] = None,
    fragrance_family: Optional[str] = None,
    gender: Optional[str] = None,
) -> str:
    parts = [f"Shop authentic {brand} {name}"]
    if concentration:
        parts[0] += f" {concentration}"
    details = []
    if fragrance_family:
        details.append(f"{fragrance_family} fragrance")
    if gender and gender != "unisex":
        details.append(f"for {gender}")
    if details:
        parts.append(". ".join(details))
    parts.append("Free shipping available. Genuine fragrance guaranteed.")
    desc = ". ".join(parts)
    return desc[:160]


def extract_keywords(
    brand: str,
    name: str,
    concentration: Optional[str] = None,
    fragrance_family: Optional[str] = None,
    notes: Optional[list] = None,
    gender: Optional[str] = None,
) -> list[str]:
    keywords = [
        brand.lower(),
        name.lower(),
        f"{brand} {name}".lower(),
        "fragrance",
        "perfume",
        "luxury fragrance",
        "authentic perfume",
    ]
    if concentration:
        keywords.append(concentration.lower())
        keywords.append(f"{brand} {concentration}".lower())
    if fragrance_family:
        keywords.append(fragrance_family.lower())
    if gender and gender != "unisex":
        keywords.append(f"perfume for {gender}".lower())
    if notes:
        keywords.extend([n.lower() for n in notes[:5]])
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
    return result[:20]


def build_structured_data(product: dict) -> dict:
    data = {
        "@context": "https://schema.org",
        "@type": "Product",
        "name": product.get("name", ""),
        "brand": {"@type": "Brand", "name": product.get("brand", "")},
        "description": product.get("description", ""),
        "sku": product.get("sku", ""),
        "offers": {
            "@type": "Offer",
            "priceCurrency": "USD",
            "price": str(product.get("website_price", 0)),
            "availability": "https://schema.org/InStock" if product.get("inventory_status") == "in_stock" else "https://schema.org/OutOfStock",
        },
    }
    if product.get("rating_avg") and product.get("review_count"):
        data["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(product["rating_avg"]),
            "reviewCount": str(product["review_count"]),
        }
    return data
