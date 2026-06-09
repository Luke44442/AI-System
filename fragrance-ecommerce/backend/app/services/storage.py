from __future__ import annotations
import uuid
from pathlib import Path
from typing import BinaryIO, Optional
import boto3
from botocore.client import Config
from app.config import settings


def _get_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.R2_ENDPOINT_URL,
        aws_access_key_id=settings.R2_ACCESS_KEY_ID,
        aws_secret_access_key=settings.R2_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_file(
    file_obj: BinaryIO,
    filename: str,
    content_type: str = "application/octet-stream",
    folder: str = "products",
) -> str:
    client = _get_client()
    ext = Path(filename).suffix
    key = f"{folder}/{uuid.uuid4().hex}{ext}"
    client.upload_fileobj(
        file_obj,
        settings.R2_BUCKET_NAME,
        key,
        ExtraArgs={"ContentType": content_type},
    )
    return f"{settings.R2_PUBLIC_URL}/{key}"


def upload_from_url(source_url: str, folder: str = "products") -> Optional[str]:
    import httpx

    try:
        with httpx.Client(timeout=30) as client:
            r = client.get(source_url)
            r.raise_for_status()
            content_type = r.headers.get("content-type", "image/jpeg")
            ext = ".jpg" if "jpeg" in content_type else ".png" if "png" in content_type else ".jpg"
            key = f"{folder}/{uuid.uuid4().hex}{ext}"
            s3 = _get_client()
            import io
            s3.upload_fileobj(
                io.BytesIO(r.content),
                settings.R2_BUCKET_NAME,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            return f"{settings.R2_PUBLIC_URL}/{key}"
    except Exception:
        return None


def delete_file(url: str) -> bool:
    try:
        key = url.replace(f"{settings.R2_PUBLIC_URL}/", "")
        client = _get_client()
        client.delete_object(Bucket=settings.R2_BUCKET_NAME, Key=key)
        return True
    except Exception:
        return False


def generate_presigned_url(key: str, expires_in: int = 3600) -> str:
    client = _get_client()
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": key},
        ExpiresIn=expires_in,
    )
