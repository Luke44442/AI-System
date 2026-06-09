"""Seed demo luxury fragrance products for development."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.database import AsyncSessionLocal
from app.models.product import Brand, Category, Supplier, Product, ProductVariant
from app.services.seo import generate_product_slug, generate_seo_title, generate_seo_description, extract_keywords
from app.services.sku_generator import generate_sku
from app.services.pricing_engine import calculate_website_price, calculate_marketplace_price
from decimal import Decimal

DEMO_BRANDS = [
    {"name": "Chanel", "slug": "chanel", "is_luxury": True},
    {"name": "Dior", "slug": "dior", "is_luxury": True},
    {"name": "Tom Ford", "slug": "tom-ford", "is_luxury": True},
    {"name": "Yves Saint Laurent", "slug": "yves-saint-laurent", "is_luxury": True},
    {"name": "Gucci", "slug": "gucci", "is_luxury": True},
    {"name": "Versace", "slug": "versace", "is_luxury": True},
    {"name": "Prada", "slug": "prada", "is_luxury": True},
    {"name": "Armani", "slug": "armani", "is_luxury": True},
    {"name": "Burberry", "slug": "burberry", "is_luxury": True},
    {"name": "Creed", "slug": "creed", "is_luxury": True},
]

DEMO_PRODUCTS = [
    {
        "brand": "Chanel",
        "name": "N°5",
        "concentration": "eau de parfum",
        "volume_ml": 100,
        "gender": "female",
        "fragrance_family": "Floral Aldehyde",
        "supplier_cost": Decimal("35"),
        "top_notes": ["Aldehydes", "Ylang-ylang", "Neroli"],
        "middle_notes": ["Jasmine", "Rose", "Lily of the Valley"],
        "base_notes": ["Vetiver", "Sandalwood", "Vanilla", "Amber"],
        "launch_year": 1921,
        "description": "The legendary Chanel N°5, a timeless floral aldehyde that has captivated women for over a century. An icon of femininity and elegance.",
    },
    {
        "brand": "Dior",
        "name": "Sauvage",
        "concentration": "eau de parfum",
        "volume_ml": 100,
        "gender": "male",
        "fragrance_family": "Aromatic Fougere",
        "supplier_cost": Decimal("30"),
        "top_notes": ["Bergamot", "Pepper"],
        "middle_notes": ["Lavender", "Pink Pepper", "Vetiver"],
        "base_notes": ["Ambroxan", "Cedar", "Labdanum"],
        "launch_year": 2018,
        "description": "Dior Sauvage EDP: A radical freshness, dictated by a noble composition. A creation by perfumer Francois Demachy.",
    },
    {
        "brand": "Tom Ford",
        "name": "Black Orchid",
        "concentration": "eau de parfum",
        "volume_ml": 100,
        "gender": "unisex",
        "fragrance_family": "Oriental Floral",
        "supplier_cost": Decimal("45"),
        "top_notes": ["Truffle", "Bergamot", "Black Currant"],
        "middle_notes": ["Black Orchid", "Spices", "Dark Fruits"],
        "base_notes": ["Patchouli", "Vanilla", "Balsam", "Sandalwood"],
        "launch_year": 2006,
        "description": "Tom Ford Black Orchid is a luxurious and sensual fragrance of rare black orchids and dark opulent notes.",
    },
    {
        "brand": "Yves Saint Laurent",
        "name": "Black Opium",
        "concentration": "eau de parfum",
        "volume_ml": 90,
        "gender": "female",
        "fragrance_family": "Oriental Vanilla",
        "supplier_cost": Decimal("28"),
        "top_notes": ["Pink Pepper", "Orange Blossom"],
        "middle_notes": ["Coffee", "Jasmine"],
        "base_notes": ["Vanilla", "White Musk", "Patchouli", "Cedarwood"],
        "launch_year": 2013,
        "description": "YSL Black Opium is addictive, the perfect rock chic fragrance with electrifying coffee notes.",
    },
    {
        "brand": "Creed",
        "name": "Aventus",
        "concentration": "eau de parfum",
        "volume_ml": 100,
        "gender": "male",
        "fragrance_family": "Fruity Chypre",
        "supplier_cost": Decimal("85"),
        "top_notes": ["Pineapple", "Bergamot", "Black Currant", "Apple"],
        "middle_notes": ["Birch", "Patchouli", "Moroccan Jasmine", "Rose"],
        "base_notes": ["Musk", "Oak Moss", "Ambergris", "Vanilla"],
        "launch_year": 2010,
        "description": "Creed Aventus celebrates strength, power, and success. A rich blend of fruity and woody notes that has become the world's most celebrated fragrance.",
    },
    {
        "brand": "Versace",
        "name": "Eros",
        "concentration": "eau de toilette",
        "volume_ml": 100,
        "gender": "male",
        "fragrance_family": "Oriental Fougere",
        "supplier_cost": Decimal("22"),
        "top_notes": ["Mint", "Green Apple", "Lemon"],
        "middle_notes": ["Tonka Bean", "Ambroxan", "Geranium"],
        "base_notes": ["Vanilla", "Vetiver", "Oakmoss", "Cedar"],
        "launch_year": 2012,
        "description": "Versace Eros is inspired by Greek mythology, a powerful and passionate fragrance for the modern man.",
    },
    {
        "brand": "Gucci",
        "name": "Bloom",
        "concentration": "eau de parfum",
        "volume_ml": 100,
        "gender": "female",
        "fragrance_family": "Floral",
        "supplier_cost": Decimal("30"),
        "top_notes": ["Rangoon Creeper"],
        "middle_notes": ["Jasmine", "Tuberose"],
        "base_notes": ["Sandalwood", "Musk"],
        "launch_year": 2017,
        "description": "Gucci Bloom is an intense floral fragrance inspired by a garden in full bloom, rich in flowers.",
    },
    {
        "brand": "Armani",
        "name": "Acqua di Gio Profumo",
        "concentration": "parfum",
        "volume_ml": 75,
        "gender": "male",
        "fragrance_family": "Aromatic Aquatic",
        "supplier_cost": Decimal("40"),
        "top_notes": ["Bergamot", "Sea Notes"],
        "middle_notes": ["Rosemary", "Incense", "Geranium"],
        "base_notes": ["Patchouli", "Vetiver", "Labdanum"],
        "launch_year": 2015,
        "description": "Acqua di Gio Profumo is a spiritual journey into the aquatic soul, combining fresh marine notes with sacred incense.",
    },
]


async def seed():
    async with AsyncSessionLocal() as db:
        from sqlalchemy import select

        brand_map = {}
        for bdata in DEMO_BRANDS:
            existing = await db.execute(select(Brand).where(Brand.slug == bdata["slug"]))
            brand = existing.scalar_one_or_none()
            if not brand:
                brand = Brand(**bdata)
                db.add(brand)
                await db.flush()
            brand_map[bdata["name"]] = brand

        supplier_result = await db.execute(select(Supplier).where(Supplier.slug == "orientdig"))
        supplier = supplier_result.scalar_one_or_none()

        for pdata in DEMO_PRODUCTS:
            brand_name = pdata.pop("brand")
            brand = brand_map.get(brand_name)
            cost = pdata["supplier_cost"]
            shipping = Decimal("8")

            sku = generate_sku(brand_name, pdata["name"], pdata.get("concentration"), pdata.get("volume_ml"), pdata.get("gender"))
            slug = generate_product_slug(brand_name, pdata["name"], pdata.get("volume_ml"), pdata.get("concentration"))

            existing = await db.execute(select(Product).where(Product.slug == slug))
            if existing.scalar_one_or_none():
                print(f"Skipping {pdata['name']} (already exists)")
                continue

            website_price = calculate_website_price(cost, shipping)
            marketplace_price = calculate_marketplace_price(cost, shipping)
            seo_keywords = extract_keywords(
                brand_name, pdata["name"],
                pdata.get("concentration"),
                pdata.get("fragrance_family"),
                (pdata.get("top_notes") or []) + (pdata.get("middle_notes") or []),
                pdata.get("gender"),
            )

            product = Product(
                sku=sku,
                slug=slug,
                name=pdata["name"],
                brand_id=brand.id if brand else None,
                supplier_id=supplier.id if supplier else None,
                concentration=pdata.get("concentration"),
                volume_ml=pdata.get("volume_ml"),
                gender=pdata.get("gender", "unisex"),
                fragrance_family=pdata.get("fragrance_family"),
                supplier_cost=cost,
                shipping_cost=shipping,
                website_price=website_price,
                marketplace_price=marketplace_price,
                inventory_status="in_stock",
                inventory_quantity=50,
                top_notes=pdata.get("top_notes"),
                middle_notes=pdata.get("middle_notes"),
                base_notes=pdata.get("base_notes"),
                launch_year=pdata.get("launch_year"),
                description=pdata.get("description"),
                seo_title=generate_seo_title(brand_name, pdata["name"], pdata.get("concentration"), pdata.get("volume_ml")),
                seo_description=generate_seo_description(brand_name, pdata["name"], pdata.get("concentration"), pdata.get("fragrance_family"), pdata.get("gender")),
                seo_keywords=seo_keywords,
                is_active=True,
                is_featured=True,
                is_new_arrival=True,
            )
            db.add(product)
            print(f"Added: {brand_name} {pdata['name']}")

        await db.commit()
        print("Seed complete!")


if __name__ == "__main__":
    asyncio.run(seed())
