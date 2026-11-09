from django.conf import settings
from django.db import models

from kreo.common.choices import ApplicationStatus, FavoriteTargetType
from kreo.common.models import UUIDPrimaryKeyModel


class Application(UUIDPrimaryKeyModel):
    """Candidature d'un membre à un rôle, avec historique immuable d'étapes."""

    role = models.ForeignKey(
        "opportunities.OpportunityRole", on_delete=models.CASCADE, related_name="applications"
    )
    applicant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications"
    )
    message = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=ApplicationStatus.choices, default=ApplicationStatus.SUBMITTED
    )
    availability_confirmed = models.BooleanField(null=True, blank=True)
    portfolio_media = models.ManyToManyField("media.MediaAsset", related_name="+", blank=True)
    attachments = models.ManyToManyField(
        "media.MediaAsset", through="ApplicationAttachment", related_name="+"
    )
    first_response_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "applications"
        constraints = [
            models.UniqueConstraint(
                fields=["role", "applicant"], name="uq_application_role_applicant"
            )
        ]
        indexes = [
            models.Index(fields=["applicant", "-submitted_at"], name="idx_apps_applicant"),
            models.Index(fields=["role", "status"], name="idx_apps_role_status"),
        ]


class ApplicationAttachment(models.Model):
    """Fichier privé joint (PDF ou image, 10 Mo max), servi par URL signée."""

    application = models.ForeignKey(Application, on_delete=models.CASCADE)
    media = models.ForeignKey("media.MediaAsset", on_delete=models.CASCADE)

    class Meta:
        db_table = "application_attachments"
        constraints = [
            models.UniqueConstraint(
                fields=["application", "media"], name="uq_application_attachment"
            )
        ]


class ApplicationEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    from_status = models.CharField(
        max_length=20, choices=ApplicationStatus.choices, null=True, blank=True
    )
    to_status = models.CharField(max_length=20, choices=ApplicationStatus.choices)
    note = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "application_events"
        ordering = ["created_at"]


class OwnerResponseStat(models.Model):
    """Délai médian de première réponse d'un porteur, recalculé chaque nuit."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="response_stat",
    )
    median_hours = models.FloatField(null=True, blank=True)
    sample_size = models.PositiveIntegerField(default=0)
    computed_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "owner_response_stats"


class Favorite(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="favorites"
    )
    target_type = models.CharField(max_length=20, choices=FavoriteTargetType.choices)
    target_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "favorites"
        constraints = [
            models.UniqueConstraint(fields=["user", "target_type", "target_id"], name="uq_favorite")
        ]


class SavedSearch(UUIDPrimaryKeyModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="saved_searches"
    )
    name = models.CharField(max_length=100, blank=True, default="")
    filters = models.JSONField()
    alerts_enabled = models.BooleanField(default=False)
    last_notified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_searches"
