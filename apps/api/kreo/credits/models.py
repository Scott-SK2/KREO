from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Coalesce, Lower

from kreo.common.choices import CreditStatus
from kreo.common.models import UUIDPrimaryKeyModel


class ProjectCredit(UUIDPrimaryKeyModel):
    """Crédit : rôle tenu sur un projet, confirmé par le porteur et par la personne.
    Peut être proposé à un e-mail non inscrit ; s'active à la création du compte."""

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="credits"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="credits",
    )
    invited_email = models.EmailField(blank=True, default="")
    role_name = models.CharField(max_length=160)
    status = models.CharField(
        max_length=20, choices=CreditStatus.choices, default=CreditStatus.PROPOSED
    )
    proposed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="credits_proposed"
    )
    dispute_reason = models.TextField(blank=True, default="")
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "project_credits"
        constraints = [
            models.CheckConstraint(
                condition=Q(user__isnull=False) | ~Q(invited_email=""), name="credit_target_present"
            ),
            models.UniqueConstraint(
                "project",
                Coalesce(models.F("user_id"), models.Value(None), output_field=models.UUIDField()),
                Lower("role_name"),
                name="credits_unique_user_role",
                condition=Q(user__isnull=False),
            ),
            models.UniqueConstraint(
                "project",
                Lower("invited_email"),
                Lower("role_name"),
                name="credits_unique_email_role",
                condition=Q(user__isnull=True),
            ),
        ]
        indexes = [models.Index(fields=["user", "status"], name="idx_credits_user")]


class CreditEvent(models.Model):
    id = models.BigAutoField(primary_key=True)
    credit = models.ForeignKey(ProjectCredit, on_delete=models.CASCADE, related_name="events")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    to_status = models.CharField(max_length=20, choices=CreditStatus.choices)
    reason = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "credit_events"
        ordering = ["created_at"]
