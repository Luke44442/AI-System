from __future__ import annotations
import re
from decimal import Decimal
from typing import Optional
import httpx
from .base import BaseSupplier, SupplierProduct

BASE_URL = "https://www.orientdig.com"


class OrientDigSupplier(BaseSupplier):
    name = "orientdig"
    base_url = BASE_URL

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self._session = httpx.Client(
            base_url=BASE_URL,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; AureviaBot/1.0)",
                "Accept-Language": "en-US,en;q=0.9",
            },
            timeout=30,
            follow_redirects=True,
        )

    def fetch_catalog(self) -> list[SupplierProduct]:
        products = []
        page = 1
        while True:
            try:
                resp = self._session.get(f"/fragrances?page={page}")
                if resp.status_code != 200:
                    break
                page_products = self._parse_catalog_page(resp.text)
                if not page_products:
                    break
                products.extend(page_products)
                page += 1
                if page > 50:
                    break
            except Exception:
                break
        return products

    def fetch_product(self, supplier_sku: str) -> Optional[SupplierProduct]:
        try:
            resp = self._session.get(f"/product/{supplier_sku}")
            if resp.status_code != 200:
                return None
            return self._parse_product_page(resp.text, supplier_sku)
        except Exception:
            return None

    def _parse_catalog_page(self, html: str) -> list[SupplierProduct]:
        products = []
        sku_pattern = re.compile(r'data-sku=["\']([^"\']+)["\']')
        name_pattern = re.compile(r'data-name=["\']([^"\']+)["\']')
        price_pattern = re.compile(r'data-price=["\']([^"\']+)["\']')

        skus = sku_pattern.findall(html)
        names = name_pattern.findall(html)
        prices = price_pattern.findall(html)

        for i, sku in enumerate(skus):
            try:
                price_str = prices[i] if i < len(prices) else "0"
                price = Decimal(re.sub(r"[^\d.]", "", price_str) or "0")
                products.append(SupplierProduct(
                    supplier_sku=sku,
                    name=names[i] if i < len(names) else sku,
                    brand=self._extract_brand(names[i] if i < len(names) else ""),
                    price=price,
                    supplier_url=f"{BASE_URL}/product/{sku}",
                ))
            except Exception:
                continue
        return products

    def _parse_product_page(self, html: str, sku: str) -> Optional[SupplierProduct]:
        name_m = re.search(r'<h1[^>]*class=["\'][^"\']*product-title[^"\']*["\'][^>]*>([^<]+)</h1>', html, re.I)
        price_m = re.search(r'class=["\'][^"\']*price[^"\']*["\'][^>]*>\$?([\d.]+)', html, re.I)
        img_m = re.findall(r'<img[^>]+src=["\']([^"\']+(?:jpg|jpeg|png|webp))["\']', html, re.I)

        if not name_m:
            return None

        name = name_m.group(1).strip()
        price = Decimal(price_m.group(1)) if price_m else Decimal("0")
        images = [u for u in img_m if "product" in u.lower()][:5]

        return SupplierProduct(
            supplier_sku=sku,
            name=name,
            brand=self._extract_brand(name),
            price=price,
            image_urls=images,
            supplier_url=f"{BASE_URL}/product/{sku}",
        )

    @staticmethod
    def _extract_brand(name: str) -> str:
        known_brands = [
            "Chanel", "Dior", "Gucci", "YSL", "Yves Saint Laurent", "Tom Ford",
            "Versace", "Prada", "Armani", "Giorgio Armani", "Burberry", "Calvin Klein",
            "Hugo Boss", "Dolce Gabbana", "Givenchy", "Hermes", "Cartier", "Creed",
            "Bvlgari", "Bulgari", "Lancome", "Narciso Rodriguez", "Marc Jacobs",
        ]
        name_lower = name.lower()
        for brand in known_brands:
            if brand.lower() in name_lower:
                return brand
        parts = name.split()
        return parts[0] if parts else "Unknown"
