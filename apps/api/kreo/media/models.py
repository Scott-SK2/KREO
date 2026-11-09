from django.conf import settings
from django.db import models

from kreo.common.choices import Visibility
from kreo.common.models import UUIDPrimaryKeyModel


class MediaAsset(UUIDPrimaryKeyModel):
    """Fichier téléversé (image ou PDF). Privé par défaut, servi par URL signée."""

    class ScanStatus(models.TextChoices):
        PENDING = "pending"
        CLEAN = "clean"
        INFECTED = "infected"
        FAILED = "failed"

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="media_assets"
    )
    storage_key = models.CharField(max_length=255, unique=True)
    mime_type = models.CharField(max_length=120)
    size_bytes = models.BigIntegerField()
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    alt_text = models.TextField(blank=True, default="")
    scan_status = models.CharField(
        max_length=20, choices=ScanStatus.choices, default=ScanStatus.PENDING
    )
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PRIVATE
    )
    # Variantes générées (3 tailles) : {"sm": key, "md": key, "lg": key}
    variants = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "media_assets"
        constraints = [
            models.CheckConstraint(
                condition=models.Q(size_bytes__gte=0), name="media_size_positive"
            )
        ]

    @property
    def is_image(self):
        return self.mime_type.startswith("image/")
