"""Product image normalization pipeline.

Every uploaded image is normalized before it hits the CDN:
  * decoded + validated (rejects non-images and decompression bombs)
  * EXIF orientation applied, then ALL metadata stripped (privacy + size)
  * resized to a maximum edge of 2000px
  * re-encoded as JPEG quality 85 (or PNG when transparency is present)
"""
from __future__ import annotations
import io
from dataclasses import dataclass

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_EDGE = 2000
JPEG_QUALITY = 85
MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB raw upload ceiling

# Refuse images that would decompress into something enormous.
Image.MAX_IMAGE_PIXELS = 60_000_000


class InvalidImageError(Exception):
    pass


@dataclass
class NormalizedImage:
    data: bytes
    content_type: str
    extension: str
    width: int
    height: int


def normalize_image(raw: bytes) -> NormalizedImage:
    if not raw:
        raise InvalidImageError("Empty file")
    if len(raw) > MAX_UPLOAD_BYTES:
        raise InvalidImageError(f"File exceeds {MAX_UPLOAD_BYTES // (1024 * 1024)}MB limit")

    try:
        img = Image.open(io.BytesIO(raw))
        img.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise InvalidImageError(f"Not a valid image: {exc}") from exc

    # Apply camera rotation before we strip the EXIF that encodes it.
    img = ImageOps.exif_transpose(img)

    if img.width > MAX_EDGE or img.height > MAX_EDGE:
        img.thumbnail((MAX_EDGE, MAX_EDGE), Image.LANCZOS)

    has_alpha = img.mode in ("RGBA", "LA", "P") and (
        img.mode != "P" or "transparency" in img.info
    )
    out = io.BytesIO()
    if has_alpha:
        img = img.convert("RGBA")
        # Re-save without the original info dict → metadata stripped.
        img.save(out, format="PNG", optimize=True)
        content_type, extension = "image/png", ".png"
    else:
        img = img.convert("RGB")
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
        content_type, extension = "image/jpeg", ".jpg"

    return NormalizedImage(
        data=out.getvalue(),
        content_type=content_type,
        extension=extension,
        width=img.width,
        height=img.height,
    )
