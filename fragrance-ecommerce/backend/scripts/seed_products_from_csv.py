"""Seed all fragrance products from the Best Perfume Spreadsheet CSV data."""
import asyncio
import re
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from decimal import Decimal
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.product import Brand, Supplier, Product
from app.services.seo import generate_product_slug, generate_seo_title, generate_seo_description, extract_keywords
from app.services.sku_generator import generate_sku
from app.services.pricing_engine import calculate_website_price, calculate_marketplace_price

# ---------------------------------------------------------------------------
# Brand metadata: default gender, fragrance family, luxury flag, image pool
# ---------------------------------------------------------------------------
BRAND_META = {
    "Tom Ford": {
        "is_luxury": True,
        "slug": "tom-ford",
        "default_gender": "unisex",
        "default_family": "Oriental",
        "images": [
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&q=80",
            "https://images.unsplash.com/photo-1541614101331-1a5a3a194e92?w=800&q=80",
        ],
    },
    "Dior": {
        "is_luxury": True,
        "slug": "dior",
        "default_gender": "unisex",
        "default_family": "Aromatic Fougere",
        "images": [
            "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=800&q=80",
            "https://images.unsplash.com/photo-1595425959494-aa7049f1a6b6?w=800&q=80",
        ],
    },
    "Viktor & Rolf": {
        "is_luxury": True,
        "slug": "viktor-rolf",
        "default_gender": "male",
        "default_family": "Oriental Spicy",
        "images": [
            "https://images.unsplash.com/photo-1587017539504-67cfbddac569?w=800&q=80",
        ],
    },
    "Paco Rabanne": {
        "is_luxury": False,
        "slug": "paco-rabanne",
        "default_gender": "male",
        "default_family": "Oriental Fougere",
        "images": [
            "https://images.unsplash.com/photo-1573575154488-36b0b0d8c97e?w=800&q=80",
        ],
    },
    "Mancera": {
        "is_luxury": True,
        "slug": "mancera",
        "default_gender": "unisex",
        "default_family": "Oriental Floral",
        "images": [
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&q=80",
        ],
    },
    "Maison Francis Kurkdjian": {
        "is_luxury": True,
        "slug": "maison-francis-kurkdjian",
        "default_gender": "unisex",
        "default_family": "Floral Oriental",
        "images": [
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&q=80",
            "https://images.unsplash.com/photo-1560869713-da86a9ec0744?w=800&q=80",
        ],
    },
    "Acqua Di Parma": {
        "is_luxury": True,
        "slug": "acqua-di-parma",
        "default_gender": "unisex",
        "default_family": "Citrus Aromatic",
        "images": [
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&q=80",
        ],
    },
    "Versace": {
        "is_luxury": False,
        "slug": "versace",
        "default_gender": "unisex",
        "default_family": "Oriental Fougere",
        "images": [
            "https://images.unsplash.com/photo-1547007831-c52d3c5cc7b7?w=800&q=80",
        ],
    },
    "Prada": {
        "is_luxury": True,
        "slug": "prada",
        "default_gender": "female",
        "default_family": "Floral Fruity",
        "images": [
            "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=800&q=80",
        ],
    },
    "Azzaro": {
        "is_luxury": False,
        "slug": "azzaro",
        "default_gender": "male",
        "default_family": "Aromatic Woody",
        "images": [
            "https://images.unsplash.com/photo-1573575154488-36b0b0d8c97e?w=800&q=80",
        ],
    },
    "Creed": {
        "is_luxury": True,
        "slug": "creed",
        "default_gender": "male",
        "default_family": "Fruity Chypre",
        "images": [
            "https://images.unsplash.com/photo-1590156562745-5ed0d38c9cd5?w=800&q=80",
            "https://images.unsplash.com/photo-1541614101331-1a5a3a194e92?w=800&q=80",
        ],
    },
    "Initio": {
        "is_luxury": True,
        "slug": "initio",
        "default_gender": "unisex",
        "default_family": "Oriental Musky",
        "images": [
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&q=80",
        ],
    },
    "Valentino": {
        "is_luxury": True,
        "slug": "valentino",
        "default_gender": "unisex",
        "default_family": "Floral Woody",
        "images": [
            "https://images.unsplash.com/photo-1595425959494-aa7049f1a6b6?w=800&q=80",
        ],
    },
    "Hermes": {
        "is_luxury": True,
        "slug": "hermes",
        "default_gender": "male",
        "default_family": "Woody Earthy",
        "images": [
            "https://images.unsplash.com/photo-1560869713-da86a9ec0744?w=800&q=80",
        ],
    },
    "Chanel": {
        "is_luxury": True,
        "slug": "chanel",
        "default_gender": "unisex",
        "default_family": "Floral Aldehyde",
        "images": [
            "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?w=800&q=80",
            "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=800&q=80",
        ],
    },
    "YSL": {
        "is_luxury": True,
        "slug": "yves-saint-laurent",
        "default_gender": "female",
        "default_family": "Oriental Vanilla",
        "images": [
            "https://images.unsplash.com/photo-1595425959494-aa7049f1a6b6?w=800&q=80",
        ],
    },
    "Penhaligon's": {
        "is_luxury": True,
        "slug": "penhaligons",
        "default_gender": "unisex",
        "default_family": "Floral Oriental",
        "images": [
            "https://images.unsplash.com/photo-1556760544-74068565f05c?w=800&q=80",
        ],
    },
    "Le Labo": {
        "is_luxury": True,
        "slug": "le-labo",
        "default_gender": "unisex",
        "default_family": "Woody Musky",
        "images": [
            "https://images.unsplash.com/photo-1541614101331-1a5a3a194e92?w=800&q=80",
        ],
    },
    "Byredo": {
        "is_luxury": True,
        "slug": "byredo",
        "default_gender": "unisex",
        "default_family": "Floral Woody Musk",
        "images": [
            "https://images.unsplash.com/photo-1563170351-be82bc888aa4?w=800&q=80",
        ],
    },
    "Maison Margiela": {
        "is_luxury": True,
        "slug": "maison-margiela",
        "default_gender": "unisex",
        "default_family": "Aromatic",
        "images": [
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&q=80",
            "https://images.unsplash.com/photo-1547007831-c52d3c5cc7b7?w=800&q=80",
        ],
    },
    "L'Artisan": {
        "is_luxury": True,
        "slug": "lartisan-parfumeur",
        "default_gender": "unisex",
        "default_family": "Green Floral",
        "images": [
            "https://images.unsplash.com/photo-1556760544-74068565f05c?w=800&q=80",
        ],
    },
    "Dolce & Gabbana": {
        "is_luxury": False,
        "slug": "dolce-gabbana",
        "default_gender": "unisex",
        "default_family": "Aquatic Floral",
        "images": [
            "https://images.unsplash.com/photo-1573575154488-36b0b0d8c97e?w=800&q=80",
        ],
    },
    "Xerjoff": {
        "is_luxury": True,
        "slug": "xerjoff",
        "default_gender": "unisex",
        "default_family": "Oriental Woody",
        "images": [
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&q=80",
        ],
    },
    "Jean Paul Gaultier": {
        "is_luxury": False,
        "slug": "jean-paul-gaultier",
        "default_gender": "male",
        "default_family": "Oriental Fougere",
        "images": [
            "https://images.unsplash.com/photo-1590156562745-5ed0d38c9cd5?w=800&q=80",
        ],
    },
    "Louis Vuitton": {
        "is_luxury": True,
        "slug": "louis-vuitton",
        "default_gender": "unisex",
        "default_family": "Floral Oriental",
        "images": [
            "https://images.unsplash.com/photo-1560869713-da86a9ec0744?w=800&q=80",
            "https://images.unsplash.com/photo-1507652313519-d4e9174996dd?w=800&q=80",
        ],
    },
    "Emporio Armani": {
        "is_luxury": False,
        "slug": "emporio-armani",
        "default_gender": "male",
        "default_family": "Aromatic Aquatic",
        "images": [
            "https://images.unsplash.com/photo-1588776814546-1ffcf47267a5?w=800&q=80",
        ],
    },
    "Parfums De Marly": {
        "is_luxury": True,
        "slug": "parfums-de-marly",
        "default_gender": "unisex",
        "default_family": "Oriental Floral",
        "images": [
            "https://images.unsplash.com/photo-1556760544-74068565f05c?w=800&q=80",
            "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&q=80",
        ],
    },
    "Carolina Herrera": {
        "is_luxury": False,
        "slug": "carolina-herrera",
        "default_gender": "male",
        "default_family": "Aromatic Woody",
        "images": [
            "https://images.unsplash.com/photo-1587017539504-67cfbddac569?w=800&q=80",
        ],
    },
    "Billie Eilish": {
        "is_luxury": False,
        "slug": "billie-eilish",
        "default_gender": "female",
        "default_family": "Floral Musky",
        "images": [
            "https://images.unsplash.com/photo-1595425959494-aa7049f1a6b6?w=800&q=80",
        ],
    },
}

# ---------------------------------------------------------------------------
# Streetwear / Sneaker brand metadata (OrientDig supplier)
# ---------------------------------------------------------------------------
STREETWEAR_BRAND_META = {
    "Nike": {
        "is_luxury": False,
        "slug": "nike",
        "images": [
            "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=800&q=80",
            "https://images.unsplash.com/photo-1600269452121-4f2416e55c28?w=800&q=80",
        ],
    },
    "Jordan": {
        "is_luxury": False,
        "slug": "jordan",
        "images": [
            "https://images.unsplash.com/photo-1607522370275-f14206abe5d3?w=800&q=80",
            "https://images.unsplash.com/photo-1556906781-9a412961a28c?w=800&q=80",
        ],
    },
    "Balenciaga": {
        "is_luxury": True,
        "slug": "balenciaga",
        "images": [
            "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=800&q=80",
        ],
    },
    "Rick Owens": {
        "is_luxury": True,
        "slug": "rick-owens",
        "images": [
            "https://images.unsplash.com/photo-1582588678413-dbf45f4823e9?w=800&q=80",
        ],
    },
    "Louis Vuitton Bags": {
        "is_luxury": True,
        "slug": "louis-vuitton-bags",
        "images": [
            "https://images.unsplash.com/photo-1548036328-c9fa89d128fa?w=800&q=80",
            "https://images.unsplash.com/photo-1584917865442-de89df76afd3?w=800&q=80",
        ],
    },
    "Spider": {
        "is_luxury": False,
        "slug": "sp5der",
        "images": [
            "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
        ],
    },
    "Gallery Dept": {
        "is_luxury": True,
        "slug": "gallery-dept",
        "images": [
            "https://images.unsplash.com/photo-1523381294911-8d3cead13475?w=800&q=80",
        ],
    },
    "Amiri": {
        "is_luxury": True,
        "slug": "amiri",
        "images": [
            "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=800&q=80",
        ],
    },
    "Essentials": {
        "is_luxury": False,
        "slug": "fear-of-god-essentials",
        "images": [
            "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=800&q=80",
        ],
    },
    "Supreme": {
        "is_luxury": False,
        "slug": "supreme",
        "images": [
            "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=800&q=80",
        ],
    },
    "Stussy": {
        "is_luxury": False,
        "slug": "stussy",
        "images": [
            "https://images.unsplash.com/photo-1618354691373-d851c5c3a990?w=800&q=80",
        ],
    },
    "Bape": {
        "is_luxury": False,
        "slug": "bape",
        "images": [
            "https://images.unsplash.com/photo-1565084888279-aca607ecce0c?w=800&q=80",
        ],
    },
    "Trapstar": {
        "is_luxury": False,
        "slug": "trapstar",
        "images": [
            "https://images.unsplash.com/photo-1556821840-3a63f15732ce?w=800&q=80",
        ],
    },
    "Off-White": {
        "is_luxury": True,
        "slug": "off-white",
        "images": [
            "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=800&q=80",
        ],
    },
    "Corteiz": {
        "is_luxury": False,
        "slug": "corteiz",
        "images": [
            "https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=800&q=80",
        ],
    },
    "Palace": {
        "is_luxury": False,
        "slug": "palace",
        "images": [
            "https://images.unsplash.com/photo-1529374255404-311a2a4f1fd9?w=800&q=80",
        ],
    },
}

# ---------------------------------------------------------------------------
# Streetwear / Sneaker products from OrientDig CSV
# Format: (brand, name, cost_str, product_type, category)
# product_type: 'shoes' | 'clothing' | 'accessories'
# ---------------------------------------------------------------------------
STREETWEAR_PRODUCTS = [
    # Nike Dunks
    ("Nike", "Dunk Low Retro White Black Panda", "32.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Retro Black White", "32.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low University Blue", "38.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Green Noise", "38.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Championship Red", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Veneer", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Retro Gorge Green", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk High Retro White Green Strike", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk High Retro Black White", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Next Nature Hemp", "38.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Pale Ivory", "38.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Smoke Grey", "38.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low Lemon Drop", "42.00", "shoes", "Sneakers"),
    ("Nike", "Dunk Low SE 85", "42.00", "shoes", "Sneakers"),
    ("Nike", "SB Dunk Low Pro", "45.00", "shoes", "Sneakers"),
    ("Nike", "SB Dunk High Pro", "45.00", "shoes", "Sneakers"),
    ("Nike", "Air Force 1 Low White", "32.00", "shoes", "Sneakers"),
    ("Nike", "Air Force 1 Low Black", "32.00", "shoes", "Sneakers"),
    ("Nike", "Air Force 1 Low Triple White", "35.00", "shoes", "Sneakers"),
    ("Nike", "Air Max 90 White", "42.00", "shoes", "Sneakers"),
    ("Nike", "Air Max 97 Silver Bullet", "55.00", "shoes", "Sneakers"),
    ("Nike", "Air Max 1 Anniversary Red", "55.00", "shoes", "Sneakers"),
    ("Nike", "Cortez White Black", "32.00", "shoes", "Sneakers"),
    # Jordan
    ("Jordan", "Air Jordan 4 Retro White Cement", "69.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 4 Retro Black Cat", "69.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 4 Retro Military Blue", "70.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 4 Retro Fire Red", "70.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 4 Retro Bred Reimagined", "70.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 4 Retro Thunder", "70.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 1 Retro High OG Chicago", "65.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 1 Retro High OG Bred Toe", "65.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 1 Low OG Shadow", "55.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 3 Retro White Cement Reimagined", "65.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 3 Retro Black Cement", "65.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 11 Retro Cherry", "75.00", "shoes", "Sneakers"),
    ("Jordan", "Air Jordan 11 Retro Bred", "75.00", "shoes", "Sneakers"),
    # Balenciaga
    ("Balenciaga", "Triple S Sneaker White", "73.00", "shoes", "Sneakers"),
    ("Balenciaga", "Triple S Sneaker Black", "73.00", "shoes", "Sneakers"),
    ("Balenciaga", "Track Runner Sneaker", "73.00", "shoes", "Sneakers"),
    ("Balenciaga", "Speed Trainer Black", "65.00", "shoes", "Sneakers"),
    # Rick Owens
    ("Rick Owens", "Ramones Low Top Sneaker", "35.00", "shoes", "Sneakers"),
    ("Rick Owens", "Geth Runner Sneaker", "35.00", "shoes", "Sneakers"),
    ("Rick Owens", "DRKSHDW Detroit Sneaker", "35.00", "shoes", "Sneakers"),
    # Louis Vuitton Bags
    ("Louis Vuitton Bags", "Neverfull MM Monogram Tote", "103.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Speedy 30 Monogram", "85.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Speedy 25 Monogram", "78.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Alma PM Monogram", "95.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Pochette Accessories Monogram", "73.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Onthego GM Monogram", "103.00", "accessories", "Bags"),
    ("Louis Vuitton Bags", "Keepall 55 Bandouliere Monogram", "103.00", "accessories", "Bags"),
    # Spider Worldwide
    ("Spider", "Worldwide Hoodie Black", "38.00", "clothing", "Hoodies"),
    ("Spider", "Worldwide Hoodie White", "38.00", "clothing", "Hoodies"),
    ("Spider", "Worldwide Hoodie Pink", "38.00", "clothing", "Hoodies"),
    ("Spider", "Web Jogger Sweatpants Black", "35.00", "clothing", "Sweatpants"),
    ("Spider", "Web Jogger Sweatpants Grey", "35.00", "clothing", "Sweatpants"),
    ("Spider", "Worldwide Tee Black", "22.00", "clothing", "T-Shirts"),
    ("Spider", "Worldwide Tee White", "22.00", "clothing", "T-Shirts"),
    # Gallery Dept
    ("Gallery Dept", "Painted Logo Hoodie", "55.00", "clothing", "Hoodies"),
    ("Gallery Dept", "Art Dept Tee Vintage White", "35.00", "clothing", "T-Shirts"),
    ("Gallery Dept", "Art Dept Tee Black", "35.00", "clothing", "T-Shirts"),
    ("Gallery Dept", "Painted Flare Jeans Blue", "75.00", "clothing", "Jeans"),
    # Amiri
    ("Amiri", "MX1 Jeans Indigo", "85.00", "clothing", "Jeans"),
    ("Amiri", "Shotgun Jeans Black", "85.00", "clothing", "Jeans"),
    ("Amiri", "Core Logo Tee White", "42.00", "clothing", "T-Shirts"),
    ("Amiri", "Core Logo Tee Black", "42.00", "clothing", "T-Shirts"),
    # Fear of God Essentials
    ("Essentials", "Pullover Hoodie Cream", "35.00", "clothing", "Hoodies"),
    ("Essentials", "Pullover Hoodie Black", "35.00", "clothing", "Hoodies"),
    ("Essentials", "Pullover Hoodie Grey", "35.00", "clothing", "Hoodies"),
    ("Essentials", "Sweatpants Cream", "32.00", "clothing", "Sweatpants"),
    ("Essentials", "Sweatpants Black", "32.00", "clothing", "Sweatpants"),
    ("Essentials", "Tee Cream", "22.00", "clothing", "T-Shirts"),
    ("Essentials", "Tee Black", "22.00", "clothing", "T-Shirts"),
    # Supreme
    ("Supreme", "Box Logo Hoodie Black", "55.00", "clothing", "Hoodies"),
    ("Supreme", "Box Logo Hoodie Red", "55.00", "clothing", "Hoodies"),
    ("Supreme", "Box Logo Tee White", "28.00", "clothing", "T-Shirts"),
    ("Supreme", "Box Logo Tee Black", "28.00", "clothing", "T-Shirts"),
    ("Supreme", "Embroidered Logo Crewneck Grey", "45.00", "clothing", "Sweatshirts"),
    # Stussy
    ("Stussy", "Basic Tee White", "18.00", "clothing", "T-Shirts"),
    ("Stussy", "Basic Tee Black", "18.00", "clothing", "T-Shirts"),
    ("Stussy", "8 Ball Hoodie Black", "38.00", "clothing", "Hoodies"),
    ("Stussy", "Patterned Bucket Hat", "22.00", "clothing", "Hats"),
    # Bape
    ("Bape", "Shark Hoodie Zip-Up Blue Camo", "55.00", "clothing", "Hoodies"),
    ("Bape", "Shark Hoodie Zip-Up Green Camo", "55.00", "clothing", "Hoodies"),
    ("Bape", "ABC Camo Tee", "28.00", "clothing", "T-Shirts"),
    ("Bape", "ABC Camo Hoodie", "50.00", "clothing", "Hoodies"),
    # Trapstar
    ("Trapstar", "Chenille Decoded Hoodie Black", "45.00", "clothing", "Hoodies"),
    ("Trapstar", "Chenille Decoded Tracksuit Black", "85.00", "clothing", "Tracksuits"),
    ("Trapstar", "Irongate T-Shirt Black", "25.00", "clothing", "T-Shirts"),
    # Off-White
    ("Off-White", "Diagonal Stripe Tee White", "45.00", "clothing", "T-Shirts"),
    ("Off-White", "Diagonal Stripe Tee Black", "45.00", "clothing", "T-Shirts"),
    ("Off-White", "Industrial Belt Hoodie", "65.00", "clothing", "Hoodies"),
    # Corteiz
    ("Corteiz", "Alcatraz Hoodie Black", "38.00", "clothing", "Hoodies"),
    ("Corteiz", "Alcatraz Hoodie Grey", "38.00", "clothing", "Hoodies"),
    ("Corteiz", "Rules The World Tee", "22.00", "clothing", "T-Shirts"),
    ("Corteiz", "4Starz Cargo Pants", "48.00", "clothing", "Pants"),
    # Palace
    ("Palace", "Tri-Ferg Hoodie Blue", "42.00", "clothing", "Hoodies"),
    ("Palace", "Tri-Ferg Tee White", "25.00", "clothing", "T-Shirts"),
    ("Palace", "Tri-Ferg Tee Black", "25.00", "clothing", "T-Shirts"),
]

# ---------------------------------------------------------------------------
# All products parsed from the Best Perfume Spreadsheet CSV
# Format: (brand, name, cost_str)
# ---------------------------------------------------------------------------
CSV_PRODUCTS = [
    # Tom Ford
    ("Tom Ford", "Oud Wood", "6.53"),
    ("Tom Ford", "Rose Prick", "7.25"),
    ("Tom Ford", "Bitter Peach", "7.25"),
    ("Tom Ford", "Tobacco Vanille", "7.98"),
    ("Tom Ford", "Fucking Fabulous", "7.25"),
    ("Tom Ford", "White Suede", "7.25"),
    ("Tom Ford", "Rose Exposed", "7.98"),
    ("Tom Ford", "Soleil Blanc", "7.25"),
    ("Tom Ford", "Cafe Rose", "9.43"),
    ("Tom Ford", "Grey Vetiver", "7.98"),
    # Dior
    ("Dior", "Homme Cologne", "6.97"),
    ("Dior", "Homme Intense", "6.97"),
    ("Dior", "Homme", "6.97"),
    ("Dior", "Sauvage Eau De Toilette", "6.97"),
    ("Dior", "Sauvage Eau De Parfum", "6.97"),
    ("Dior", "Sauvage Elixir", "6.97"),
    ("Dior", "Sauvage Parfum", "6.97"),
    ("Dior", "Hypnotic Poison", "6.97"),
    ("Dior", "Addict", "6.97"),
    ("Dior", "Oud Ispahan", "6.97"),
    ("Dior", "Higher Energy", "6.97"),
    ("Dior", "Joy", "6.97"),
    ("Dior", "Lucky", "6.97"),
    ("Dior", "Sakura", "6.97"),
    ("Dior", "Gris Dior", "6.97"),
    ("Dior", "La Colle Noire", "6.97"),
    ("Dior", "J'adore", "6.97"),
    ("Dior", "Miss Dior Blooming Bouquet", "6.97"),
    ("Dior", "Addict Eau Fraiche", "6.97"),
    ("Dior", "Bois D'argent", "6.97"),
    ("Dior", "Rose Kabuki", "6.97"),
    ("Dior", "Balade Sauvage", "6.97"),
    # Viktor & Rolf
    ("Viktor & Rolf", "Spicebomb Extreme", "8.94"),
    ("Viktor & Rolf", "Spicebomb Eau De Toilette", "8.94"),
    ("Viktor & Rolf", "Spicebomb Night Vision", "8.94"),
    ("Viktor & Rolf", "Spicebomb Infrared", "8.94"),
    ("Viktor & Rolf", "Spicebomb Dark Leather", "8.94"),
    ("Viktor & Rolf", "Spicebomb Metallic Musk", "8.94"),
    ("Viktor & Rolf", "Flowerbomb", "8.94"),
    # Paco Rabanne
    ("Paco Rabanne", "Invictus Victory Eau De Parfum Extreme", "8.49"),
    ("Paco Rabanne", "Invictus Victory Elixir Perfume Intense", "8.49"),
    ("Paco Rabanne", "Invictus Victory Legend Eau De Parfum", "8.49"),
    ("Paco Rabanne", "Invictus Victory Parfum", "8.49"),
    ("Paco Rabanne", "Invictus Victory Eau De Toilette", "8.49"),
    ("Paco Rabanne", "One Million Eau De Toilette", "6.19"),
    ("Paco Rabanne", "One Million Elixir", "7.74"),
    ("Paco Rabanne", "One Million Parfum", "7.74"),
    ("Paco Rabanne", "One Million Lucky", "7.74"),
    ("Paco Rabanne", "One Million Royal", "7.74"),
    ("Paco Rabanne", "One Million Lady", "7.74"),
    ("Paco Rabanne", "Phantom Perfume", "8.51"),
    ("Paco Rabanne", "Phantom Fame", "8.51"),
    ("Paco Rabanne", "Phantom Eau De Toilette", "8.51"),
    ("Paco Rabanne", "Phantom Fame Blooming Pink", "8.51"),
    ("Paco Rabanne", "Phantom Intense", "8.51"),
    # Mancera
    ("Mancera", "Purple Flowers", "8.94"),
    ("Mancera", "Roses Vanille", "8.94"),
    ("Mancera", "Red Tobacco", "8.94"),
    ("Mancera", "Amore Caffe", "8.94"),
    ("Mancera", "Intense Red Tobacco", "8.94"),
    ("Mancera", "Cedrat Boise", "8.94"),
    ("Mancera", "Tonka Cola", "8.94"),
    ("Mancera", "Intense Cedrat Boise", "8.94"),
    ("Mancera", "French Riviera", "8.94"),
    ("Mancera", "Xplicit Vanilla", "8.94"),
    ("Mancera", "Instant Crush", "8.94"),
    ("Mancera", "Intense Instant Crush", "8.94"),
    # Maison Francis Kurkdjian
    ("Maison Francis Kurkdjian", "Baccarat Rouge 540 Extrait De Parfum", "7.68"),
    ("Maison Francis Kurkdjian", "Baccarat Rouge 540 Eau De Parfum", "7.68"),
    ("Maison Francis Kurkdjian", "724", "7.68"),
    ("Maison Francis Kurkdjian", "Reflets D'Ambre", "7.68"),
    ("Maison Francis Kurkdjian", "Aqua Celestia", "7.68"),
    ("Maison Francis Kurkdjian", "Petit Matin", "7.68"),
    ("Maison Francis Kurkdjian", "Oud Satin Mood", "7.68"),
    ("Maison Francis Kurkdjian", "Aqua Universalis", "7.68"),
    ("Maison Francis Kurkdjian", "Aqua Media", "7.68"),
    ("Maison Francis Kurkdjian", "A La Rose", "7.68"),
    ("Maison Francis Kurkdjian", "Apom", "7.68"),
    ("Maison Francis Kurkdjian", "Oud", "7.68"),
    ("Maison Francis Kurkdjian", "Grand Soir", "7.68"),
    # Acqua Di Parma
    ("Acqua Di Parma", "Mirto Di Panarea", "7.22"),
    ("Acqua Di Parma", "Mandorlo Di Sicilia", "7.22"),
    ("Acqua Di Parma", "Arancia Di Capri", "7.22"),
    ("Acqua Di Parma", "Fico Di Amalfi", "7.22"),
    ("Acqua Di Parma", "Ginepro Di Sardegna", "7.22"),
    ("Acqua Di Parma", "Cipresso Di Toscana", "7.22"),
    ("Acqua Di Parma", "Bergamotto Di Calabria", "7.22"),
    ("Acqua Di Parma", "Chinotto Di Liguria", "7.22"),
    ("Acqua Di Parma", "Cedro Di Taormina", "7.22"),
    ("Acqua Di Parma", "Colonia Essenza", "7.22"),
    ("Acqua Di Parma", "Buongiorno", "7.22"),
    ("Acqua Di Parma", "Colonia", "7.22"),
    ("Acqua Di Parma", "IL Profumo", "7.22"),
    ("Acqua Di Parma", "Zafferano", "7.22"),
    ("Acqua Di Parma", "Quercia", "7.22"),
    ("Acqua Di Parma", "Magnolia Infinita", "7.22"),
    ("Acqua Di Parma", "Luce Di Rosa", "7.22"),
    # Versace
    ("Versace", "Eros Pour Femme Eau De Parfum", "10.04"),
    ("Versace", "Crystal Noir", "7.72"),
    ("Versace", "Eros Perfume", "7.72"),
    ("Versace", "Pour Homme", "7.72"),
    ("Versace", "Dylan Blue", "7.72"),
    ("Versace", "Eros Najim", "8.49"),
    ("Versace", "Eros Energy", "7.72"),
    ("Versace", "Pour Femme Dylan Blue", "10.04"),
    ("Versace", "Versense", "10.04"),
    ("Versace", "Bright Crystal", "8.49"),
    ("Versace", "Pour Femme Dylan Purple", "10.04"),
    ("Versace", "Eros Flame", "7.72"),
    ("Versace", "Pour Femme Dylan Turquoise", "10.04"),
    ("Versace", "Yellow Diamond", "7.72"),
    ("Versace", "Bright Crystal Absolu", "7.72"),
    # Prada
    ("Prada", "Paradoxe Eau De Parfum", "7.79"),
    ("Prada", "Paradoxe Intense", "7.79"),
    ("Prada", "Paradoxe Virtual Flower", "7.79"),
    ("Prada", "Paradoxe Radical Essence", "7.79"),
    # Azzaro
    ("Azzaro", "Most Wanted Intense", "4.06"),
    ("Azzaro", "Most Wanted Parfum", "4.06"),
    ("Azzaro", "Most Wanted By Night", "4.06"),
    ("Azzaro", "Wanted Eau De Parfum", "4.06"),
    ("Azzaro", "The Most Wanted Eau De Toilette Intense", "4.06"),
    # Creed
    ("Creed", "Aventus", "6.94"),
    ("Creed", "Himalaya", "6.94"),
    ("Creed", "Love in Black", "6.94"),
    ("Creed", "Carmina", "6.94"),
    ("Creed", "Delphinus", "6.94"),
    ("Creed", "Wind Flowers", "6.94"),
    ("Creed", "Millesime 1849", "6.94"),
    ("Creed", "Aventus Cologne", "6.94"),
    ("Creed", "Queen of Silk", "6.94"),
    ("Creed", "Centaurus", "6.94"),
    ("Creed", "Green Irish Tweed", "6.94"),
    ("Creed", "Millesime Imperial", "6.94"),
    ("Creed", "Aventus For Her", "6.94"),
    ("Creed", "10 Year Anniversary", "6.94"),
    ("Creed", "Absolu Aventus", "6.94"),
    ("Creed", "Viking", "6.94"),
    ("Creed", "Silver Mountain Water", "6.94"),
    ("Creed", "Spring Flower", "6.94"),
    ("Creed", "Virgin Island Water", "6.94"),
    ("Creed", "Love In White", "6.94"),
    # Initio
    ("Initio", "Side Effect", "11.31"),
    ("Initio", "Psychedelic Love", "11.31"),
    ("Initio", "Atomic Rose", "11.31"),
    ("Initio", "Absolute Aphrodisiac", "11.31"),
    ("Initio", "Paragon", "11.31"),
    ("Initio", "Musk Therapy", "11.31"),
    ("Initio", "Oud For Greatness", "11.31"),
    ("Initio", "Oud For Happiness", "11.31"),
    # Valentino
    ("Valentino", "Uomo Born In Roma", "3.87"),
    ("Valentino", "Uomo Born In Roma Green Stravaganza", "3.87"),
    ("Valentino", "Uomo Born In Roma Yellow Dream", "3.87"),
    ("Valentino", "Uomo Born In Roma The Gold", "3.87"),
    ("Valentino", "Uomo Born In Roma Rockstud Noir", "3.87"),
    ("Valentino", "Donna Born In Roma Coral Fantasy", "3.87"),
    ("Valentino", "Donna Born In Roma Eau De Parfum", "3.87"),
    ("Valentino", "Donna Born In Roma Pink PP", "3.87"),
    ("Valentino", "Donna Born In Roma Intense", "3.87"),
    ("Valentino", "Donna Born In Roma The Gold", "3.87"),
    ("Valentino", "Donna Born In Roma Yellow Dream", "3.87"),
    ("Valentino", "Donna Born In Roma Green Stravaganza", "3.87"),
    ("Valentino", "Valentino Uomo Extreme", "3.87"),
    ("Valentino", "Valentino Pour Femme", "3.87"),
    # Hermes
    ("Hermes", "Barenia", "9.43"),
    ("Hermes", "Terre d'Hermes", "6.96"),
    ("Hermes", "Terre Le Jardin De Monsieur Li", "6.53"),
    ("Hermes", "Terre Un Jardin Sur Le Nil", "6.53"),
    # Chanel
    ("Chanel", "Bleu De Chanel", "6.46"),
    ("Chanel", "Bleu De Chanel Eau De Parfum", "6.46"),
    ("Chanel", "Bleu De Chanel Parfum", "6.46"),
    ("Chanel", "Allure Homme Sport", "6.46"),
    ("Chanel", "Chance Eau Tendre", "6.46"),
    ("Chanel", "Chance Fraiche Eau Tendre", "6.46"),
    ("Chanel", "1957", "7.90"),
    ("Chanel", "Gabrielle", "6.46"),
    ("Chanel", "Gabrielle Essence", "6.46"),
    ("Chanel", "Coco Eau De Parfum", "6.46"),
    ("Chanel", "Coco Eau De Parfum Intense", "6.46"),
    ("Chanel", "Coco Eau Pour La Nuit", "6.46"),
    ("Chanel", "Coco Noir", "7.18"),
    ("Chanel", "N°5 L'Eau", "6.46"),
    ("Chanel", "N°5 L'Eau Eau De Toilette", "9.34"),
    ("Chanel", "N°5", "6.46"),
    ("Chanel", "N°6", "6.46"),
    # YSL
    ("YSL", "Mon Paris", "6.46"),
    ("YSL", "Black Opium", "6.46"),
    ("YSL", "Libre", "6.46"),
    ("YSL", "Libre Le Parfum", "6.46"),
    ("YSL", "Libre Absolu Platine", "8.62"),
    ("YSL", "Myslf", "9.34"),
    ("YSL", "Y Eau De Toilette", "6.90"),
    # Penhaligon's
    ("Penhaligon's", "The Coveted Duchess Rose", "11.58"),
    ("Penhaligon's", "Portraits Arthur", "11.58"),
    ("Penhaligon's", "Portraits Constance", "11.58"),
    ("Penhaligon's", "Portraits Duchess Rose", "11.58"),
    ("Penhaligon's", "Portraits William", "11.58"),
    ("Penhaligon's", "Portraits Mister Thompson", "11.58"),
    ("Penhaligon's", "Portraits Mister Teddy", "11.58"),
    ("Penhaligon's", "Portraits Mr Sam", "11.58"),
    ("Penhaligon's", "Portraits Clara", "11.58"),
    ("Penhaligon's", "Portraits Lord George", "11.58"),
    # Le Labo
    ("Le Labo", "Another 13", "7.18"),
    ("Le Labo", "The Noir 29", "7.18"),
    ("Le Labo", "Rose 31", "7.18"),
    ("Le Labo", "Santal 33", "7.18"),
    ("Le Labo", "Gaiac 10", "7.18"),
    ("Le Labo", "Bergamote 22", "7.18"),
    ("Le Labo", "The Matcha 26", "7.18"),
    ("Le Labo", "Patchouli 24", "7.18"),
    ("Le Labo", "Vetiver 46", "7.18"),
    ("Le Labo", "Iris 39", "7.18"),
    # Byredo
    ("Byredo", "La Tulipe", "6.74"),
    ("Byredo", "Rose of No Man's Land", "6.74"),
    ("Byredo", "Super Cedar", "6.74"),
    ("Byredo", "Blanche", "6.74"),
    ("Byredo", "Mojave Ghost", "6.74"),
    ("Byredo", "Gypsy Water", "6.74"),
    ("Byredo", "Bal D'Afrique", "6.74"),
    ("Byredo", "Inflorescence", "6.74"),
    ("Byredo", "Young Rose", "6.74"),
    ("Byredo", "Animalique", "6.74"),
    ("Byredo", "Open Sky", "6.74"),
    ("Byredo", "Mixed Emotions", "6.74"),
    ("Byredo", "Bibliotheque", "6.74"),
    ("Byredo", "Lil Fleur", "6.74"),
    ("Byredo", "Space Rage", "6.74"),
    # Maison Margiela
    ("Maison Margiela", "On A Date", "8.49"),
    ("Maison Margiela", "Autumn Vibes", "6.49"),
    ("Maison Margiela", "At The Barber's", "6.49"),
    ("Maison Margiela", "Beach Walk", "6.49"),
    ("Maison Margiela", "Bubble Bath", "6.49"),
    ("Maison Margiela", "When The Rain Stops", "6.49"),
    ("Maison Margiela", "Coffee Break", "6.49"),
    ("Maison Margiela", "Under The Stars", "6.49"),
    ("Maison Margiela", "Wicked Love", "9.27"),
    ("Maison Margiela", "By The Fireplace", "6.49"),
    ("Maison Margiela", "Flower Market", "6.49"),
    ("Maison Margiela", "Flying", "9.27"),
    ("Maison Margiela", "Tea Escape", "6.49"),
    ("Maison Margiela", "Jazz Club", "6.49"),
    ("Maison Margiela", "Lazy Sunday Morning", "6.49"),
    ("Maison Margiela", "Whispers In The Library", "6.49"),
    ("Maison Margiela", "Matcha Meditation", "6.49"),
    ("Maison Margiela", "Dancing On The Moon", "9.27"),
    ("Maison Margiela", "Music Festival", "6.49"),
    ("Maison Margiela", "Sailing Day", "6.49"),
    ("Maison Margiela", "Lipstick On", "6.49"),
    ("Maison Margiela", "Funfair Evening", "6.49"),
    ("Maison Margiela", "Springtime In A Park", "6.49"),
    ("Maison Margiela", "From The Garden", "6.49"),
    ("Maison Margiela", "Under The Lemon Trees", "6.49"),
    ("Maison Margiela", "Soul Of The Forest", "9.27"),
    ("Maison Margiela", "Across Sands", "9.27"),
    # L'Artisan
    ("L'Artisan", "Passage D'Enfer", "8.20"),
    ("L'Artisan", "Fou D'Absinthe", "8.20"),
    ("L'Artisan", "La Chasse Aux Papillons", "8.20"),
    ("L'Artisan", "Voleur De Roses", "8.20"),
    ("L'Artisan", "Premier Figuier", "8.20"),
    ("L'Artisan", "L'Ete En Douce", "8.20"),
    ("L'Artisan", "Timbuktu", "8.20"),
    ("L'Artisan", "Bucoliques De Provence", "8.20"),
    ("L'Artisan", "Le Chant De Camargue", "8.20"),
    ("L'Artisan", "Passage D'Enfer Extreme", "8.20"),
    ("L'Artisan", "Dzongkha", "8.20"),
    ("L'Artisan", "Memoire De Roses", "8.20"),
    ("L'Artisan", "26 Tenebrae", "8.20"),
    ("L'Artisan", "9 Arcana Rosa", "8.20"),
    ("L'Artisan", "25 Obscuratio", "8.20"),
    ("L'Artisan", "32 Venenum", "8.20"),
    ("L'Artisan", "60 Mirabilis", "8.20"),
    ("L'Artisan", "63 Crepusculum", "8.20"),
    ("L'Artisan", "Il Etait Un Bois", "8.20"),
    ("L'Artisan", "Un Air De Bretagne", "8.20"),
    # Dolce & Gabbana
    ("Dolce & Gabbana", "Light Blue", "7.74"),
    ("Dolce & Gabbana", "Q Eau De Parfum", "7.74"),
    ("Dolce & Gabbana", "Devotion", "7.74"),
    ("Dolce & Gabbana", "K Eau De Parfum", "7.74"),
    ("Dolce & Gabbana", "K Eau De Toilette", "7.74"),
    ("Dolce & Gabbana", "Light Blue Forever", "7.74"),
    ("Dolce & Gabbana", "Light Blue Eau Intense", "7.74"),
    ("Dolce & Gabbana", "The One Lady", "7.74"),
    ("Dolce & Gabbana", "The One Men", "7.74"),
    ("Dolce & Gabbana", "L'Imperatrice", "7.74"),
    # Xerjoff
    ("Xerjoff", "Opera", "9.99"),
    ("Xerjoff", "Groove Xcape", "12.29"),
    ("Xerjoff", "Vibe Erba Gold", "10.76"),
    ("Xerjoff", "Wardasina", "10.76"),
    ("Xerjoff", "Erba Pura", "10.76"),
    ("Xerjoff", "Accento", "10.76"),
    ("Xerjoff", "Soprano", "9.99"),
    ("Xerjoff", "Coro", "9.99"),
    ("Xerjoff", "Alexandria II", "12.29"),
    ("Xerjoff", "Blue Hope", "18.43"),
    ("Xerjoff", "Muse", "18.43"),
    ("Xerjoff", "Accento Overdose", "18.43"),
    ("Xerjoff", "Naxos", "18.43"),
    ("Xerjoff", "Verde Accento", "18.43"),
    ("Xerjoff", "Iommi Monkey Special", "18.43"),
    # Jean Paul Gaultier
    ("Jean Paul Gaultier", "Le Beau", "9.22"),
    ("Jean Paul Gaultier", "La Belle", "9.22"),
    ("Jean Paul Gaultier", "Paradise Garden", "9.22"),
    ("Jean Paul Gaultier", "So Scandal", "9.22"),
    ("Jean Paul Gaultier", "Scandal", "9.22"),
    ("Jean Paul Gaultier", "La Belle Paradise Garden", "9.22"),
    ("Jean Paul Gaultier", "Le Male In The Navy", "9.22"),
    ("Jean Paul Gaultier", "Le Male Elixir", "9.22"),
    ("Jean Paul Gaultier", "Le Male", "9.22"),
    ("Jean Paul Gaultier", "Divine", "9.29"),
    ("Jean Paul Gaultier", "Le Male Le Parfum", "9.29"),
    ("Jean Paul Gaultier", "Ultra Male", "9.29"),
    # Louis Vuitton (1:1 quality)
    ("Louis Vuitton", "Attrape Reves", "20.12"),
    ("Louis Vuitton", "City Of Stars", "20.12"),
    ("Louis Vuitton", "Coeur Battant", "20.12"),
    ("Louis Vuitton", "Fleur Du Desert", "20.12"),
    ("Louis Vuitton", "California Dream", "20.12"),
    ("Louis Vuitton", "Heures D'Absence", "20.12"),
    ("Louis Vuitton", "Imagination", "20.12"),
    ("Louis Vuitton", "L'Immensite", "20.12"),
    ("Louis Vuitton", "Le Jour Leve", "20.12"),
    ("Louis Vuitton", "Les Sables Roses", "20.12"),
    ("Louis Vuitton", "Au Hasard", "20.12"),
    ("Louis Vuitton", "Matiere Noire", "20.12"),
    ("Louis Vuitton", "Nuit De Feu", "20.12"),
    ("Louis Vuitton", "Ombre Nomade", "20.12"),
    ("Louis Vuitton", "Pacific Chill", "20.12"),
    ("Louis Vuitton", "Pur Oud", "20.12"),
    ("Louis Vuitton", "Rose Des Vents", "20.12"),
    ("Louis Vuitton", "Spell On You", "20.12"),
    ("Louis Vuitton", "On The Beach", "20.12"),
    ("Louis Vuitton", "Apogee", "20.12"),
    ("Louis Vuitton", "Sur La Route", "20.12"),
    ("Louis Vuitton", "Dans La Peau", "20.12"),
    ("Louis Vuitton", "Contre Moi", "20.12"),
    ("Louis Vuitton", "Orage", "20.12"),
    # Emporio Armani
    ("Emporio Armani", "In Love With You", "2.98"),
    ("Emporio Armani", "Because It's You", "2.98"),
    ("Emporio Armani", "Stronger With You", "2.98"),
    ("Emporio Armani", "Stronger With You Intensely", "2.98"),
    ("Emporio Armani", "Stronger With You Absolutely", "2.98"),
    ("Emporio Armani", "Stronger With You Oud", "2.98"),
    ("Emporio Armani", "Stronger With You Amber", "2.98"),
    ("Emporio Armani", "Stronger With You Sandalwood", "2.98"),
    ("Emporio Armani", "Stronger With You Tobacco", "2.98"),
    ("Emporio Armani", "Stronger With You Parfum", "2.98"),
    ("Emporio Armani", "My Way", "2.98"),
    ("Emporio Armani", "Acqua Di Gio Pour Homme", "7.81"),
    ("Emporio Armani", "Acqua Di Gio Elixir", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Profumo", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Profondo", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Absolu", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Eau De Parfum", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Parfum", "8.95"),
    ("Emporio Armani", "Acqua Di Gio Absolu Instinct", "8.95"),
    # Parfums De Marly
    ("Parfums De Marly", "Altair", "8.49"),
    ("Parfums De Marly", "Layton", "7.72"),
    ("Parfums De Marly", "Godolphin", "7.72"),
    ("Parfums De Marly", "Haltane", "7.72"),
    ("Parfums De Marly", "Edition Royale", "7.72"),
    ("Parfums De Marly", "Greenley", "7.72"),
    ("Parfums De Marly", "Habdan", "7.72"),
    ("Parfums De Marly", "Herod", "7.72"),
    ("Parfums De Marly", "Kalan", "7.72"),
    ("Parfums De Marly", "Perseus", "7.72"),
    ("Parfums De Marly", "Pegasus", "7.72"),
    ("Parfums De Marly", "Percival", "7.72"),
    ("Parfums De Marly", "Cassili", "8.49"),
    ("Parfums De Marly", "Delina", "8.49"),
    ("Parfums De Marly", "Delina La Rosee", "8.49"),
    ("Parfums De Marly", "Delina Exclusif", "7.72"),
    ("Parfums De Marly", "Oriana", "7.72"),
    ("Parfums De Marly", "Palatine", "7.72"),
    ("Parfums De Marly", "Safanad", "7.72"),
    ("Parfums De Marly", "Valaya", "7.72"),
    # Carolina Herrera
    ("Carolina Herrera", "Bad Boy Dazzling Garden", "8.51"),
    ("Carolina Herrera", "Bad Boy Cobalt", "8.51"),
    ("Carolina Herrera", "Bad Boy Elixir", "8.51"),
    ("Carolina Herrera", "212 Men Eau De Toilette", "8.51"),
    ("Carolina Herrera", "212 Sexy Men", "10.06"),
    ("Carolina Herrera", "212 Vip", "10.06"),
    ("Carolina Herrera", "212 Vip Red", "10.06"),
    ("Carolina Herrera", "212 Heroes Forever Young", "10.06"),
    ("Carolina Herrera", "212 Sexy", "10.06"),
    ("Carolina Herrera", "Bad Boy It's So Good To Be Bad", "8.51"),
    ("Carolina Herrera", "Bad Boy", "8.51"),
    # Billie Eilish
    ("Billie Eilish", "Eau De Parfum", "10.06"),
    ("Billie Eilish", "Eau De Parfum No 2", "10.06"),
    ("Billie Eilish", "Eau De Parfum No 3", "10.06"),
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_CONC_PATTERNS = [
    (re.compile(r"\bextrait\s+de\s+parfum\b", re.I), "extrait de parfum"),
    (re.compile(r"\bextrait\b", re.I), "extrait de parfum"),
    (re.compile(r"\beau\s+de\s+parfum\s+intense\b", re.I), "eau de parfum intense"),
    (re.compile(r"\beau\s+de\s+parfum\b", re.I), "eau de parfum"),
    (re.compile(r"\beau\s+de\s+toilette\s+intense\b", re.I), "eau de toilette intense"),
    (re.compile(r"\beau\s+de\s+toilette\b", re.I), "eau de toilette"),
    (re.compile(r"\bparfum\s+intense\b", re.I), "parfum intense"),
    (re.compile(r"\bparfum\b", re.I), "parfum"),
    (re.compile(r"\belixir\b", re.I), "elixir"),
    (re.compile(r"\bcologne\b", re.I), "cologne"),
    (re.compile(r"\beau\s+fraiche\b", re.I), "eau fraiche"),
]

_FEMALE_HINTS = re.compile(
    r"\b(femme|donna|lady|bloom|fleur|rose|floral|belle|divine|coral|"
    r"flowerbomb|opium|libre|mon paris|j.adore|miss dior|joy|sakura|"
    r"gabrielle|coco|chance|pink|bouquet|spring flower|love in white|"
    r"wind flowers|queen|spring|light blue|delina|cassili|oriana|valaya|"
    r"my way|in love|because it.s you|flowerbomb|versense|bright crystal|"
    r"yellow diamond|crystal noir|sexy|scandal|la belle)\b",
    re.I,
)
_MALE_HINTS = re.compile(
    r"\b(homme|pour homme|man|men|viking|sauvage|eros|invictus|phantom|"
    r"one million|bleu|aventus|silver mountain|millesime|herod|layton|"
    r"pegasus|godolphin|altair|kalan|habdan|greenley|herod|percy|"
    r"spicebomb|le male|ultra male|bad boy|acqua di gio|stronger with you|"
    r"allure homme|grey vetiver|tobacco vanille|oud wood|himalaya|"
    r"green irish tweed|centaurus|barenia|terre|dylan blue|k eau)\b",
    re.I,
)


def _detect_concentration(name: str) -> str:
    for pattern, label in _CONC_PATTERNS:
        if pattern.search(name):
            return label
    return "eau de parfum"


def _detect_gender(brand: str, name: str, brand_default: str) -> str:
    combined = f"{brand} {name}".lower()
    if _FEMALE_HINTS.search(combined):
        return "female"
    if _MALE_HINTS.search(combined):
        return "male"
    return brand_default


def _clean_name(name: str, concentration: str) -> str:
    """Strip the concentration suffix from the display name."""
    conc_map = {
        "extrait de parfum": ["extrait de parfum", "extrait"],
        "eau de parfum intense": ["eau de parfum intense"],
        "eau de parfum": ["eau de parfum", "edp"],
        "eau de toilette intense": ["eau de toilette intense"],
        "eau de toilette": ["eau de toilette", "edt"],
        "parfum intense": ["parfum intense"],
        "parfum": ["parfum"],
        "elixir": ["elixir"],
        "cologne": ["cologne"],
        "eau fraiche": ["eau fraiche"],
    }
    suffixes = conc_map.get(concentration, [])
    cleaned = name
    for s in suffixes:
        cleaned = re.sub(r"\s+" + re.escape(s) + r"\s*$", "", cleaned, flags=re.I).strip()
    return cleaned


def _pick_image(meta: dict, idx: int) -> str:
    images = meta.get("images", [])
    if not images:
        return "https://images.unsplash.com/photo-1541614101331-1a5a3a194e92?w=800&q=80"
    return images[idx % len(images)]


SHIPPING = Decimal("8")
STREETWEAR_SHIPPING = Decimal("12")

# Size runs per product type, used as variant axes / size_options.
_SNEAKER_SIZES = ["7", "7.5", "8", "8.5", "9", "9.5", "10", "10.5", "11", "11.5", "12"]
_APPAREL_SIZES = ["S", "M", "L", "XL", "XXL"]

# Common colour words to extract from a product name.
_COLOR_WORDS = [
    "black", "white", "red", "blue", "green", "pink", "grey", "gray", "cream",
    "brown", "tan", "purple", "yellow", "orange", "navy", "beige", "silver", "gold",
]

# Map a clothing style category to its garment_type attribute value.
_GARMENT_TYPE_MAP = {
    "Hoodies": "Hoodie", "T-Shirts": "T-Shirt", "Sweatshirts": "Sweatshirt",
    "Sweatpants": "Sweatpants", "Jeans": "Jeans", "Pants": "Pants",
    "Tracksuits": "Tracksuit", "Hats": "Hat",
}


def _extract_color(name: str) -> str | None:
    lowered = name.lower()
    for c in _COLOR_WORDS:
        if c in lowered:
            return c.title()
    return None


def _streetwear_attributes(product_type: str, style_cat: str, raw_name: str) -> tuple[dict, list]:
    """Derive the category attributes JSONB and size_options for a streetwear product."""
    color = _extract_color(raw_name)
    attrs: dict = {}
    size_opts: list = []

    if product_type == "shoes":
        size_opts = _SNEAKER_SIZES
        attrs["silhouette"] = style_cat  # e.g. "Sneakers"
        if color:
            attrs["colorway"] = color
    elif product_type == "clothing":
        size_opts = _APPAREL_SIZES
        attrs["garment_type"] = _GARMENT_TYPE_MAP.get(style_cat, style_cat)
        attrs["fit"] = "Regular"
        if color:
            attrs["color"] = color
    elif product_type == "accessories":
        if style_cat == "Bags":
            attrs["bag_type"] = "Tote"
            attrs["material"] = "Leather"
        else:
            attrs["accessory_type"] = style_cat
        if color:
            attrs["color"] = color

    return attrs, size_opts


async def seed():
    async with AsyncSessionLocal() as db:
        # Ensure fragrance brands exist
        brand_map: dict[str, object] = {}
        for brand_name, meta in BRAND_META.items():
            from app.models.product import Brand
            result = await db.execute(select(Brand).where(Brand.slug == meta["slug"]))
            brand = result.scalar_one_or_none()
            if not brand:
                display_name = brand_name
                if brand_name == "YSL":
                    display_name = "Yves Saint Laurent"
                elif brand_name == "MFK":
                    display_name = "Maison Francis Kurkdjian"
                brand = Brand(
                    name=display_name,
                    slug=meta["slug"],
                    is_luxury=meta["is_luxury"],
                    is_active=True,
                )
                db.add(brand)
                await db.flush()
                print(f"  Brand created: {display_name}")
            brand_map[brand_name] = brand

        # Ensure streetwear brands exist
        for brand_name, meta in STREETWEAR_BRAND_META.items():
            from app.models.product import Brand
            result = await db.execute(select(Brand).where(Brand.slug == meta["slug"]))
            brand = result.scalar_one_or_none()
            if not brand:
                brand = Brand(
                    name=brand_name,
                    slug=meta["slug"],
                    is_luxury=meta.get("is_luxury", False),
                    is_active=True,
                )
                db.add(brand)
                await db.flush()
                print(f"  Brand created: {brand_name}")
            brand_map[brand_name] = brand

        # Get or create fragrance supplier
        from app.models.product import Supplier
        sup_result = await db.execute(select(Supplier).where(Supplier.slug == "perfume-resells"))
        supplier = sup_result.scalar_one_or_none()
        if not supplier:
            supplier = Supplier(
                name="Perfume Resells",
                slug="perfume-resells",
                type="wholesale",
                default_shipping_cost=Decimal("8"),
                avg_processing_days=3,
                avg_shipping_days=14,
                is_active=True,
            )
            db.add(supplier)
            await db.flush()

        # Get or create streetwear supplier
        sw_sup_result = await db.execute(select(Supplier).where(Supplier.slug == "orient-dig"))
        sw_supplier = sw_sup_result.scalar_one_or_none()
        if not sw_supplier:
            sw_supplier = Supplier(
                name="OrientDig",
                slug="orient-dig",
                type="wholesale",
                default_shipping_cost=Decimal("12"),
                avg_processing_days=5,
                avg_shipping_days=21,
                is_active=True,
            )
            db.add(sw_supplier)
            await db.flush()

        # Load (or create) the top-level categories so products can be assigned.
        from app.models.product import Category
        category_map: dict[str, object] = {}
        category_defs = [
            ("Fragrances", "fragrances", "fragrance"),
            ("Sneakers", "sneakers", "sneakers"),
            ("Streetwear", "streetwear", "clothing"),
            ("Designer Clothing", "designer-clothing", "clothing"),
            ("Bags", "bags", "bags"),
            ("Accessories", "accessories", "accessories"),
            ("Watches", "watches", "watches"),
            ("Jewelry", "jewelry", "jewelry"),
        ]
        for cat_name, cat_slug, schema_type in category_defs:
            cat_res = await db.execute(select(Category).where(Category.slug == cat_slug))
            cat = cat_res.scalar_one_or_none()
            if not cat:
                cat = Category(name=cat_name, slug=cat_slug, attribute_schema_type=schema_type, is_active=True)
                db.add(cat)
                await db.flush()
                print(f"  Category created: {cat_name}")
            category_map[cat_slug] = cat

        def _streetwear_category_slug(product_type: str, style_cat: str) -> str:
            if product_type == "shoes":
                return "sneakers"
            if product_type == "accessories":
                return "bags" if style_cat == "Bags" else "accessories"
            return "streetwear"  # clothing → streetwear

        added = 0
        skipped = 0
        brand_counter: dict[str, int] = {}

        for brand_name, raw_name, cost_str in CSV_PRODUCTS:
            meta = BRAND_META.get(brand_name, {
                "is_luxury": False,
                "slug": brand_name.lower().replace(" ", "-").replace("'", ""),
                "default_gender": "unisex",
                "default_family": "Floral",
                "images": [],
            })

            cost = Decimal(cost_str)
            concentration = _detect_concentration(raw_name)
            gender = _detect_gender(brand_name, raw_name, meta["default_gender"])
            display_name = _clean_name(raw_name, concentration)

            brand_obj = brand_map.get(brand_name)
            brand_display = brand_name if brand_name != "YSL" else "Yves Saint Laurent"

            slug = generate_product_slug(brand_display, display_name, 100, concentration)

            from app.models.product import Product
            existing = await db.execute(select(Product).where(Product.slug == slug))
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            sku = generate_sku(brand_display, display_name, concentration, 100, gender)
            website_price = calculate_website_price(cost, SHIPPING)
            marketplace_price = calculate_marketplace_price(cost, SHIPPING)
            seo_keywords = extract_keywords(brand_display, display_name, concentration, meta["default_family"], [], gender)

            idx = brand_counter.get(brand_name, 0)
            brand_counter[brand_name] = idx + 1
            image_url = _pick_image(meta, idx)

            fragrance_category = category_map.get("fragrances")
            gender_label = {"male": "Men", "female": "Women"}.get(gender, "Unisex")
            product = Product(
                sku=sku,
                slug=slug,
                name=display_name,
                brand_id=brand_obj.id if brand_obj else None,
                category_id=fragrance_category.id if fragrance_category else None,
                supplier_id=supplier.id,
                concentration=concentration,
                volume_ml=100,
                gender=gender,
                fragrance_family=meta["default_family"],
                supplier_cost=cost,
                shipping_cost=SHIPPING,
                website_price=website_price,
                marketplace_price=marketplace_price,
                inventory_status="in_stock",
                inventory_quantity=50,
                images=[{"url": image_url, "alt": f"{brand_display} {display_name}", "is_primary": True}],
                seo_title=generate_seo_title(brand_display, display_name, concentration, 100),
                seo_description=generate_seo_description(brand_display, display_name, concentration, meta["default_family"], gender),
                seo_keywords=seo_keywords,
                attributes={
                    "concentration": concentration.title(),
                    "fragrance_family": meta["default_family"],
                    "volume_ml": "100",
                    "gender": gender_label,
                },
                is_active=True,
                is_featured=(cost >= Decimal("7")),
                is_new_arrival=True,
            )
            db.add(product)
            added += 1

            if added % 50 == 0:
                await db.flush()
                print(f"  Flushed {added} products...")

        # Seed streetwear / sneakers / accessories
        for brand_name, raw_name, cost_str, product_type, style_cat in STREETWEAR_PRODUCTS:
            sw_meta = STREETWEAR_BRAND_META.get(brand_name, {
                "is_luxury": False,
                "slug": brand_name.lower().replace(" ", "-"),
                "images": [],
            })

            cost = Decimal(cost_str)
            brand_obj = brand_map.get(brand_name)
            brand_display = brand_name if brand_name != "Louis Vuitton Bags" else "Louis Vuitton"

            slug_name = raw_name.lower().replace(" ", "-").replace("'", "").replace("/", "-")
            slug = f"{sw_meta['slug']}-{slug_name}"[:200]

            from app.models.product import Product
            existing = await db.execute(select(Product).where(Product.slug == slug))
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            website_price = calculate_website_price(cost, STREETWEAR_SHIPPING)
            marketplace_price = calculate_marketplace_price(cost, STREETWEAR_SHIPPING)

            idx = brand_counter.get(brand_name, 0)
            brand_counter[brand_name] = idx + 1
            image_url = _pick_image(sw_meta, idx)

            cat_slug = _streetwear_category_slug(product_type, style_cat)
            category_obj = category_map.get(cat_slug)
            attrs, size_opts = _streetwear_attributes(product_type, style_cat, raw_name)

            product = Product(
                sku=f"SW-{brand_display[:4].upper()}-{idx:04d}",
                slug=slug,
                name=raw_name,
                brand_id=brand_obj.id if brand_obj else None,
                category_id=category_obj.id if category_obj else None,
                supplier_id=sw_supplier.id,
                product_type=product_type,
                style_category=style_cat,
                size_options=size_opts,
                concentration=None,
                volume_ml=None,
                gender="unisex",
                fragrance_family=None,
                supplier_cost=cost,
                shipping_cost=STREETWEAR_SHIPPING,
                website_price=website_price,
                marketplace_price=marketplace_price,
                inventory_status="in_stock",
                inventory_quantity=30,
                images=[{"url": image_url, "alt": f"{brand_display} {raw_name}", "is_primary": True}],
                seo_title=f"{brand_display} {raw_name} | Aurevia",
                seo_description=f"Shop authentic {brand_display} {raw_name}. Premium quality {style_cat.lower()} at the best prices.",
                seo_keywords=[brand_display.lower(), raw_name.lower(), style_cat.lower(), product_type],
                tags=[style_cat.lower(), product_type, brand_display.lower()],
                attributes=attrs,
                is_active=True,
                is_featured=(cost >= Decimal("50")),
                is_new_arrival=True,
            )
            db.add(product)
            added += 1

            if added % 50 == 0:
                await db.flush()
                print(f"  Flushed {added} products...")

        await db.commit()
        print(f"\nSeed complete: {added} added, {skipped} already existed")


if __name__ == "__main__":
    asyncio.run(seed())
