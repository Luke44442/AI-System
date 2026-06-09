from __future__ import annotations
import re
from decimal import Decimal
from typing import Optional
import httpx
from .base import BaseSupplier, SupplierProduct

BASE_URL = "https://www.cnshopper.com"


class CNShopperSupplier(BaseSupplier):
    name = "cnshopper"
    base_url = BASE_URL

    def __init__(self, credentials: dict):
        super().__init__(credentials)
        self._session = httpx.Client(
            base_url=BASE_URL,
            headers={"User-Agent": "Mozilla/5.0 (compatible; ScentaraBot/1.0)"},
            timeout=30,
            follow_redirects=True,
        )

    def fetch_catalog(self) -> list[SupplierProduct]:
        products = []
        categories = ["perfume", "cologne", "eau-de-parfum"]
        for cat in categories:
            page = 1
            while page <= 30:
                try:
                    resp = self._session.get(f"/{cat}?page={page}")
                    if resp.status_code != 200:
                        break
                    page_products = self._parse_listing(resp.text)
                    if not page_products:
                        break
                    products.extend(page_products)
                    page += 1
                except Exception:
                    break
        return products

    def fetch_product(self, supplier_sku: str) -> Optional[SupplierProduct]:
        try:
            resp = self._session.get(f"/product/{supplier_sku}")
            if resp.status_code != 200:
                return None
            return self._parse_detail(resp.text, supplier_sku)
        except Exception:
            return None

    def _parse_listing(self, html: str) -> list[SupplierProduct]:
        products = []
        entries = re.findall(
            r'<div[^>]+class=["\'][^"\']*product-item[^"\']*["\'][^>]*>(.*?)</div>\s*</div>',
            html, re.S | re.I
        )
        for entry in entries[:50]:
            try:
                sku_m = re.search(r'data-id=["\'](\d+)["\']', entry)
                name_m = re.search(r'<[^>]+class=["\'][^"\']*product-name[^"\']*["\'][^>]*>([^<]+)<', entry, re.I)
                price_m = re.search(r'\$([\d.]+)', entry)
                if not (sku_m and name_m and price_m):
                    continue
                products.append(SupplierProduct(
                    supplier_sku=sku_m.group(1),
                    name=name_m.group(1).strip(),
                    brand=name_m.group(1).split()[0] if name_m else "Unknown",
                    price=Decimal(price_m.group(1)),
                    supplier_url=f"{BASE_URL}/product/{sku_m.group(1)}",
                ))
            except Exception:
                continue
        return products

    def _parse_detail(self, html: str, sku: str) -> Optional[SupplierProduct]:
        name_m = re.search(r'<h1[^>]*>([^<]+)</h1>', html, re.I)
        price_m = re.search(r'id=["\']product-price["\'][^>]*>\$?([\d.]+)', html, re.I)
        stock_m = re.search(r'In Stock.*?(\d+)', html, re.I)
        imgs = re.findall(r'<img[^>]+data-src=["\']([^"\']+)["\']', html, re.I)

        if not name_m:
            return None

        return SupplierProduct(
            supplier_sku=sku,
            name=name_m.group(1).strip(),
            brand=name_m.group(1).split()[0],
            price=Decimal(price_m.group(1)) if price_m else Decimal("0"),
            image_urls=imgs[:5],
            in_stock=bool(stock_m),
            stock_qty=int(stock_m.group(1)) if stock_m else None,
            supplier_url=f"{BASE_URL}/product/{sku}",
        )
