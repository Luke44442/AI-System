from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class SupplierProduct:
    supplier_sku: str
    name: str
    brand: str
    price: Decimal
    image_urls: list[str] = field(default_factory=list)
    concentration: Optional[str] = None
    volume_ml: Optional[int] = None
    gender: Optional[str] = None
    fragrance_family: Optional[str] = None
    description: Optional[str] = None
    top_notes: Optional[list[str]] = None
    middle_notes: Optional[list[str]] = None
    base_notes: Optional[list[str]] = None
    in_stock: bool = True
    stock_qty: Optional[int] = None
    supplier_url: Optional[str] = None
    raw_data: dict = field(default_factory=dict)


class BaseSupplier(ABC):
    name: str = "base"
    base_url: str = ""

    def __init__(self, credentials: dict):
        self.credentials = credentials

    @abstractmethod
    def fetch_catalog(self) -> list[SupplierProduct]:
        pass

    @abstractmethod
    def fetch_product(self, supplier_sku: str) -> Optional[SupplierProduct]:
        pass

    def check_stock(self, supplier_sku: str) -> bool:
        product = self.fetch_product(supplier_sku)
        return product.in_stock if product else False
