"""
Abstraction de stockage : disque local en dev, Cloudflare R2 (S3) en staging/prod.
Les URL de lecture sont signées et valables 5 minutes.
"""

import hashlib
import hmac
import time
from pathlib import Path

from django.conf import settings
from django.core.files.storage import default_storage


def put(storage_key: str, content) -> None:
    default_storage.save(storage_key, content)


def delete(storage_key: str) -> None:
    if default_storage.exists(storage_key):
        default_storage.delete(storage_key)


def open_file(storage_key: str):
    return default_storage.open(storage_key, "rb")


def _signature(storage_key: str, expires: int) -> str:
    msg = f"{storage_key}:{expires}".encode()
    return hmac.new(settings.SECRET_KEY.encode(), msg, hashlib.sha256).hexdigest()[:32]


def signed_url(storage_key: str, ttl: int | None = None) -> str:
    ttl = ttl or settings.MEDIA_SIGNED_URL_TTL_SECONDS
    expires = int(time.time()) + ttl
    sig = _signature(storage_key, expires)
    return f"{settings.API_URL}/api/v1/media/file/{storage_key}?expires={expires}&sig={sig}"


def verify_signature(storage_key: str, expires: str, sig: str) -> bool:
    try:
        expires_int = int(expires)
    except (TypeError, ValueError):
        return False
    if expires_int < time.time():
        return False
    return hmac.compare_digest(_signature(storage_key, expires_int), sig or "")


def local_path(storage_key: str) -> Path:
    return Path(default_storage.path(storage_key))
