from __future__ import annotations
import io
import re
import uuid
from decimal import Decimal
from typing import Optional
import pandas as pd
from app.services.sku_generator import generate_sku
from app.services.pricing_engine import calculate_website_price, calculate_marketplace_price
from app.services.seo import slugify, generate_product_slug, generate_seo_title, generate_seo_description, extract_keywords


_COLUMN_ALIASES = {
    "brand": ["brand", "brand_name", "make", "manufacturer"],
    "name": ["name", "product_name", "title", "product_title", "fragrance_name"],
    "concentration": ["concentration", "type", "fragrance_type", "edp_edt", "strength"],
    "volume_ml": ["volume_ml", "volume", "size", "ml", "size_ml", "capacity"],
    "gender": ["gender", "for", "sex", "target_gender"],
    "supplier_cost": ["supplier_cost", "cost", "price", "buy_price", "wholesale", "cost_price"],
    "shipping_cost": ["shipping_cost", "shipping", "ship_cost", "delivery_cost"],
    "supplier_sku": ["supplier_sku", "sku", "item_sku", "product_sku", "article"],
    "fragrance_family": ["fragrance_family", "family", "scent_family", "fragrance_type"],
    "description": ["description", "product_description", "details"],
    "top_notes": ["top_notes", "top notes", "top"],
    "middle_notes": ["middle_notes", "heart_notes", "middle notes", "heart"],
    "base_notes": ["base_notes", "base notes", "base", "dry_down"],
    "image_url": ["image_url", "image", "photo", "img_url", "picture"],
}


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    col_map = {}
    lower_cols = {c.lower().strip().replace(" ", "_"): c for c in df.columns}
    for field, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            normalized = alias.lower().replace(" ", "_")
            if normalized in lower_cols:
                col_map[lower_cols[normalized]] = field
                break
    return df.rename(columns=col_map)


def _parse_notes(value) -> Optional[list]:
    if pd.isna(value) or not value:
        return None
    text = str(value)
    parts = re.split(r"[,;/|]", text)
    return [p.strip().title() for p in parts if p.strip()]


def _parse_decimal(value, default: Decimal = Decimal("0")) -> Decimal:
    if pd.isna(value) or value == "":
        return default
    try:
        cleaned = re.sub(r"[^\d.]", "", str(value))
        return Decimal(cleaned) if cleaned else default
    except Exception:
        return default


def _parse_int(value, default: int = 0) -> Optional[int]:
    if pd.isna(value) or value == "":
        return None
    try:
        return int(float(str(value)))
    except Exception:
        return None


def load_spreadsheet(file_bytes: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        try:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(io.BytesIO(file_bytes), encoding="latin-1")
    else:
        df = pd.read_excel(io.BytesIO(file_bytes))
    df = df.dropna(how="all")
    return _normalize_columns(df)


def row_to_product(row: pd.Series, supplier_id: Optional[uuid.UUID] = None, brand_id: Optional[uuid.UUID] = None) -> dict:
    brand = str(row.get("brand", "")).strip() or "Unknown"
    name = str(row.get("name", "")).strip()
    if not name:
        return {}

    concentration = str(row.get("concentration", "")).strip() or None
    volume_ml = _parse_int(row.get("volume_ml"))
    gender = str(row.get("gender", "unisex")).strip().lower()
    gender = gender if gender in ("male", "female", "unisex") else "unisex"

    supplier_cost = _parse_decimal(row.get("supplier_cost"), Decimal("0"))
    shipping_cost = _parse_decimal(row.get("shipping_cost"), Decimal("8"))

    website_price = calculate_website_price(supplier_cost, shipping_cost) if supplier_cost else None
    marketplace_price = calculate_marketplace_price(supplier_cost, shipping_cost) if supplier_cost else None

    slug = generate_product_slug(brand, name, volume_ml, concentration)
    sku = generate_sku(brand, name, concentration, volume_ml, gender)

    top_notes = _parse_notes(row.get("top_notes"))
    middle_notes = _parse_notes(row.get("middle_notes"))
    base_notes = _parse_notes(row.get("base_notes"))

    all_notes = (top_notes or []) + (middle_notes or []) + (base_notes or [])
    fragrance_family = str(row.get("fragrance_family", "")).strip() or None

    seo_title = generate_seo_title(brand, name, concentration, volume_ml)
    seo_description = generate_seo_description(brand, name, concentration, fragrance_family, gender)
    keywords = extract_keywords(brand, name, concentration, fragrance_family, all_notes, gender)

    return {
        "sku": sku,
        "name": name,
        "slug": slug,
        "brand_name": brand,
        "brand_id": brand_id,
        "supplier_id": supplier_id,
        "concentration": concentration,
        "volume_ml": volume_ml,
        "gender": gender,
        "fragrance_family": fragrance_family,
        "supplier_cost": float(supplier_cost) if supplier_cost else None,
        "shipping_cost": float(shipping_cost),
        "website_price": float(website_price) if website_price else None,
        "marketplace_price": float(marketplace_price) if marketplace_price else None,
        "supplier_sku": str(row.get("supplier_sku", "")).strip() or None,
        "description": str(row.get("description", "")).strip() or None,
        "top_notes": top_notes,
        "middle_notes": middle_notes,
        "base_notes": base_notes,
        "seo_title": seo_title,
        "seo_description": seo_description,
        "seo_keywords": keywords,
        "images": [{"url": str(row.get("image_url", "")).strip()}] if row.get("image_url") and not pd.isna(row.get("image_url")) else [],
        "is_active": True,
    }


def parse_spreadsheet(file_bytes: bytes, filename: str, supplier_id: Optional[uuid.UUID] = None) -> tuple[list[dict], list[str]]:
    df = load_spreadsheet(file_bytes, filename)
    products = []
    errors = []

    for idx, row in df.iterrows():
        try:
            product = row_to_product(row, supplier_id=supplier_id)
            if product:
                products.append(product)
            else:
                errors.append(f"Row {idx + 2}: missing required 'name' field")
        except Exception as e:
            errors.append(f"Row {idx + 2}: {str(e)}")

    return products, errors
