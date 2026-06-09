"""Thin wrapper around app/services/storage.py for use outside the FastAPI context."""
from app.services.storage import upload_file, upload_from_url, delete_file, generate_presigned_url

__all__ = ["upload_file", "upload_from_url", "delete_file", "generate_presigned_url"]
