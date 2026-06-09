from __future__ import annotations
import re
import uuid
from typing import Optional


_CONCENTRATION_MAP = {
    "parfum": "PF",
    "extrait de parfum": "EP",
    "eau de parfum": "EDP",
    "edp": "EDP",
    "eau de toilette": "EDT",
    "edt": "EDT",
    "eau de cologne": "EDC",
    "edc": "EDC",
    "body spray": "BS",
}

_GENDER_MAP = {"male": "M", "men": "M", "female": "F", "women": "F", "unisex": "U"}


def _slugify(text: str, max_len: int = 6) -> str:
    text = re.sub(r"[^a-zA-Z0-9]", "", text).upper()
    return text[:max_len]


def generate_sku(
    brand_name: str,
    product_name: str,
    concentration: Optional[str] = None,
    volume_ml: Optional[int] = None,
    gender: Optional[str] = None,
) -> str:
    brand_part = _slugify(brand_name, 4)
    name_part = _slugify(product_name, 6)

    conc_part = ""
    if concentration:
        conc_part = _CONCENTRATION_MAP.get(concentration.lower(), _slugify(concentration, 3))

    vol_part = f"{volume_ml}ML" if volume_ml else ""
    gender_part = _GENDER_MAP.get((gender or "unisex").lower(), "U")

    uid_part = uuid.uuid4().hex[:4].upper()

    parts = [p for p in [brand_part, name_part, conc_part, vol_part, gender_part, uid_part] if p]
    return "-".join(parts)


def generate_variant_sku(base_sku: str, volume_ml: int) -> str:
    uid = uuid.uuid4().hex[:4].upper()
    return f"{base_sku}-{volume_ml}ML-{uid}"
