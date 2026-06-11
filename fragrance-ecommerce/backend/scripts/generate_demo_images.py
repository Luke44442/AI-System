"""Generate local studio-style product photography for the demo catalog.

The sandbox blocks external image CDNs, so we render luxury 'studio shot'
bottle images with Pillow: gradient backdrop, glass bottle with tinted juice,
gold cap, embossed label. Output goes to frontend/public/demo/.
"""
import math
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "demo")
os.makedirs(OUT, exist_ok=True)

SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"

W, H = 900, 1200

PRODUCTS = [
    # slug-key, brand, name, backdrop RGB, juice RGB, bottle shape
    ("chanel-no5",      "CHANEL",      "N°5",                (24, 22, 20),  (212, 175, 96),  "square"),
    ("dior-sauvage",    "DIOR",        "SAUVAGE",            (16, 20, 28),  (38, 56, 84),    "tall"),
    ("tf-black-orchid", "TOM FORD",    "BLACK ORCHID",       (14, 12, 14),  (28, 22, 30),    "square"),
    ("ysl-black-opium", "YSL",         "BLACK OPIUM",        (20, 16, 22),  (40, 28, 40),    "round"),
    ("creed-aventus",   "CREED",       "AVENTUS",            (22, 24, 22),  (50, 60, 50),    "tall"),
    ("versace-eros",    "VERSACE",     "EROS",               (12, 22, 26),  (50, 130, 150),  "square"),
    ("gucci-bloom",     "GUCCI",       "BLOOM",              (28, 18, 20),  (180, 120, 130), "round"),
    ("armani-adg",      "ARMANI",      "ACQUA DI GIÒ",       (14, 18, 24),  (30, 60, 90),    "tall"),
]

CATEGORIES = [
    ("cat-fragrances",  "FRAGRANCES",        (26, 22, 18)),
    ("cat-sneakers",    "SNEAKERS",          (18, 20, 26)),
    ("cat-streetwear",  "STREETWEAR",        (22, 22, 22)),
    ("cat-designer",    "DESIGNER",          (24, 18, 22)),
    ("cat-bags",        "BAGS",              (26, 20, 16)),
    ("cat-watches",     "WATCHES",           (16, 18, 22)),
    ("cat-accessories", "ACCESSORIES",       (20, 22, 20)),
    ("cat-jewelry",     "JEWELRY",           (24, 20, 14)),
]

GOLD = (201, 168, 76)


def vertical_gradient(size, top, bottom):
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / h
        px_row = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        for x in range(w):
            px[x, y] = px_row
    return img


def radial_glow(img, center, radius, color, strength=90):
    glow = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(glow)
    cx, cy = center
    for r in range(radius, 0, -6):
        alpha = int(strength * (1 - r / radius))
        d.ellipse([cx - r, cy - r * 0.75, cx + r, cy + r * 0.75], fill=alpha)
    glow = glow.filter(ImageFilter.GaussianBlur(60))
    overlay = Image.new("RGB", img.size, color)
    img.paste(Image.composite(overlay, img, glow), (0, 0))
    return img


def draw_bottle(img, shape, juice):
    d = ImageDraw.Draw(img, "RGBA")
    cx = W // 2
    if shape == "square":
        bx0, by0, bx1, by1 = cx - 165, 430, cx + 165, 870
        cap = (cx - 60, 330, cx + 60, 440)
        neck = (cx - 42, 420, cx + 42, 470)
        rad = 22
    elif shape == "tall":
        bx0, by0, bx1, by1 = cx - 120, 380, cx + 120, 880
        cap = (cx - 48, 290, cx + 48, 388)
        neck = (cx - 34, 372, cx + 34, 420)
        rad = 30
    else:  # round
        bx0, by0, bx1, by1 = cx - 175, 470, cx + 175, 880
        cap = (cx - 52, 350, cx + 52, 470)
        neck = (cx - 36, 450, cx + 36, 500)
        rad = 110

    # floor shadow
    d.ellipse([bx0 - 40, by1 - 26, bx1 + 40, by1 + 44], fill=(0, 0, 0, 140))

    # glass body: juice fill with glassy borders
    juice_rgba = (*juice, 235)
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=rad, fill=juice_rgba,
                        outline=(255, 255, 255, 60), width=3)
    # inner glass depth
    d.rounded_rectangle([bx0 + 14, by0 + 14, bx1 - 14, by1 - 14], radius=max(rad - 10, 8),
                        outline=(255, 255, 255, 28), width=2)
    # vertical highlight strip
    d.rounded_rectangle([bx0 + 30, by0 + 30, bx0 + 70, by1 - 40], radius=18,
                        fill=(255, 255, 255, 38))
    # right rim light
    d.rounded_rectangle([bx1 - 44, by0 + 36, bx1 - 26, by1 - 50], radius=10,
                        fill=(255, 255, 255, 18))

    # neck + cap (brushed gold)
    d.rectangle(neck, fill=(120, 100, 55, 255))
    for i in range(cap[1], cap[3], 4):
        shade = 150 + int(40 * math.sin((i - cap[1]) / 7))
        d.rectangle([cap[0], i, cap[2], i + 3], fill=(shade, int(shade * 0.82), int(shade * 0.42)))
    d.rounded_rectangle(cap, radius=14, outline=(60, 48, 22), width=2)

    return (bx0, by0, bx1, by1)


def label(img, box, brand, name):
    d = ImageDraw.Draw(img, "RGBA")
    bx0, by0, bx1, by1 = box
    lx0, lx1 = bx0 + 38, bx1 - 38
    mid = (by0 + by1) // 2
    ly0, ly1 = mid - 10, mid + 130
    d.rounded_rectangle([lx0, ly0, lx1, ly1], radius=8, fill=(246, 243, 236, 248),
                        outline=(180, 170, 150, 255), width=2)
    brand_f = ImageFont.truetype(SERIF_B, 34 if len(brand) <= 8 else 27)
    name_f = ImageFont.truetype(SERIF, 26 if len(name) <= 12 else 20)
    small_f = ImageFont.truetype(SANS, 13)
    cx = (lx0 + lx1) // 2
    d.text((cx, ly0 + 34), brand, font=brand_f, fill=(30, 28, 24), anchor="mm")
    d.line([cx - 50, ly0 + 58, cx + 50, ly0 + 58], fill=GOLD, width=2)
    d.text((cx, ly0 + 84), name, font=name_f, fill=(50, 46, 40), anchor="mm")
    d.text((cx, ly0 + 116), "EAU DE PARFUM", font=small_f, fill=(120, 112, 96), anchor="mm")


def product_shot(slug, brand, name, backdrop, juice, shape):
    top = tuple(min(c + 26, 255) for c in backdrop)
    img = vertical_gradient((W, H), top, backdrop)
    img = radial_glow(img, (W // 2, 560), 430, tuple(min(c + 70, 255) for c in backdrop))
    # pedestal line
    d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 905, W, H], fill=(*tuple(max(c - 8, 0) for c in backdrop), 255))
    d.line([0, 905, W, 905], fill=(255, 255, 255, 26), width=2)

    box = draw_bottle(img, shape, juice)
    label(img, box, brand, name)

    # soft reflection
    refl = img.crop((0, 560, W, 905)).transpose(Image.FLIP_TOP_BOTTOM)
    refl = refl.resize((W, 160)).filter(ImageFilter.GaussianBlur(4))
    mask = vertical_gradient((W, 160), (70, 70, 70), (0, 0, 0)).convert("L")
    img.paste(Image.composite(refl, img.crop((0, 906, W, 1066)), mask), (0, 906))

    img.save(os.path.join(OUT, f"{slug}.jpg"), quality=88, optimize=True)
    print(f"  {slug}.jpg")


def category_tile(slug, title, base):
    img = vertical_gradient((800, 800), tuple(min(c + 34, 255) for c in base), base)
    img = radial_glow(img, (400, 430), 380, tuple(min(c + 60, 255) for c in base))
    d = ImageDraw.Draw(img, "RGBA")
    # gold corner rules for an editorial feel
    for (x0, y0, x1, y1) in [(60, 60, 200, 60), (60, 60, 60, 200),
                             (740, 740, 600, 740), (740, 740, 740, 600)]:
        d.line([x0, y0, x1, y1], fill=(*GOLD, 200), width=3)
    f = ImageFont.truetype(SERIF, 64 if len(title) <= 9 else 48)
    sub = ImageFont.truetype(SANS, 18)
    d.text((400, 380), title, font=f, fill=(244, 240, 230), anchor="mm")
    d.text((400, 450), "A U R E V I A", font=sub, fill=(*GOLD, 255), anchor="mm")
    img.save(os.path.join(OUT, f"{slug}.jpg"), quality=86, optimize=True)
    print(f"  {slug}.jpg")


if __name__ == "__main__":
    print("Product shots:")
    for p in PRODUCTS:
        product_shot(*p)
    print("Category tiles:")
    for c in CATEGORIES:
        category_tile(*c)
    print("done ->", os.path.abspath(OUT))
