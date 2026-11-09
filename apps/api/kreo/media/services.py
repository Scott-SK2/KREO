"""Pipeline médias : validation MIME et taille, quota par compte, variantes WebP."""

import io
import logging
import uuid

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from PIL import Image, UnidentifiedImageError

from kreo.common.exceptions import BusinessRuleError, ProblemException, QuotaExceededError

from . import storage
from .models import MediaAsset

logger = logging.getLogger("kreo.media")

VARIANT_SIZES = {"sm": 320, "md": 800, "lg": 1600}
MAGIC = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",
    b"%PDF": "application/pdf",
}


class UnsupportedMediaType(ProblemException):
    status_code = 415
    problem_type = "unsupported-media-type"
    default_detail = "Formats acceptés : JPEG, PNG, WebP, PDF."


class FileTooLarge(ProblemException):
    status_code = 413
    problem_type = "file-too-large"
    default_detail = "Le fichier dépasse 10 Mo."


def sniff_mime(head: bytes) -> str | None:
    for magic, mime in MAGIC.items():
        if head.startswith(magic):
            if mime == "image/webp" and head[8:12] != b"WEBP":
                continue
            return mime
    return None


def _check_quota(owner, incoming: int):
    used = MediaAsset.objects.filter(owner=owner).aggregate(s=Sum("size_bytes"))["s"] or 0
    if used + incoming > settings.MEDIA_QUOTA_BYTES_PER_ACCOUNT:
        raise QuotaExceededError(
            "Ton quota de 200 Mo est atteint. Supprime des fichiers pour en ajouter.",
            problem_type="media-quota",
        )


@transaction.atomic
def create_asset(*, owner, uploaded_file, alt_text: str = "", visibility="private") -> MediaAsset:
    if uploaded_file.size > settings.MEDIA_MAX_BYTES:
        raise FileTooLarge()
    head = uploaded_file.read(16)
    uploaded_file.seek(0)
    mime = sniff_mime(head)
    if mime is None or mime not in settings.MEDIA_ALLOWED_MIME_TYPES:
        raise UnsupportedMediaType()
    _check_quota(owner, uploaded_file.size)

    ext = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp", "application/pdf": "pdf"}[
        mime
    ]
    key = f"u/{owner.id}/{uuid.uuid4().hex}.{ext}"
    width = height = None
    variants = {}

    if mime.startswith("image/"):
        try:
            data = uploaded_file.read()
            image = Image.open(io.BytesIO(data))
            image.verify()
            image = Image.open(io.BytesIO(data))
            width, height = image.size
        except (UnidentifiedImageError, OSError):
            raise BusinessRuleError("Image illisible.", problem_type="media-corrupt")
        uploaded_file.seek(0)
        storage.put(key, uploaded_file)
        variants = _generate_variants(image, key)
    else:
        storage.put(key, uploaded_file)

    asset = MediaAsset.objects.create(
        owner=owner,
        storage_key=key,
        mime_type=mime,
        size_bytes=uploaded_file.size,
        width=width,
        height=height,
        alt_text=alt_text,
        visibility=visibility,
        variants=variants,
        # Scan antivirus asynchrone (tâche Celery) ; « clean » tant qu'aucun scanner n'est branché.
        scan_status=MediaAsset.ScanStatus.PENDING,
    )
    from .tasks import scan_asset

    scan_asset.delay(str(asset.id))
    return asset


def _generate_variants(image: Image.Image, key: str) -> dict:
    """Trois tailles WebP (320, 800, 1600 px de large)."""
    variants = {}
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    base = key.rsplit(".", 1)[0]
    for name, width in VARIANT_SIZES.items():
        copy = image.copy()
        copy.thumbnail((width, width * 4))
        buffer = io.BytesIO()
        copy.save(buffer, format="WEBP", quality=82, method=4)
        buffer.seek(0)
        variant_key = f"{base}_{name}.webp"
        storage.put(variant_key, buffer)
        variants[name] = variant_key
    return variants


def delete_asset(asset: MediaAsset) -> None:
    for key in [asset.storage_key, *asset.variants.values()]:
        storage.delete(key)
    asset.delete()


def asset_urls(asset: MediaAsset | None) -> dict | None:
    if asset is None:
        return None
    if asset.scan_status == MediaAsset.ScanStatus.INFECTED:
        return None
    return {
        "id": str(asset.id),
        "mime_type": asset.mime_type,
        "alt_text": asset.alt_text,
        "width": asset.width,
        "height": asset.height,
        "url": storage.signed_url(asset.storage_key),
        "variants": {k: storage.signed_url(v) for k, v in asset.variants.items()},
    }
