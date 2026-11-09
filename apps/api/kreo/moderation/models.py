from django.conf import settings
from django.db import models

from kreo.common.choices import AppealStatus, ReportPriority, ReportStatus, ReportTargetType
from kreo.common.models import UUIDPrimaryKeyModel


class Block(models.Model):
    """Blocage : s'applique partout (messagerie, candidatures, actualités, recherche)."""

    blocker = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_made"
    )
    blocked = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="blocks_received"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "blocks"
        constraints = [
            models.UniqueConstraint(fields=["blocker", "blocked"], name="uq_block"),
            models.CheckConstraint(
                condition=~models.Q(blocker=models.F("blocked")), name="block_not_self"
            ),
        ]


class Report(UUIDPrimaryKeyModel):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reports_made"
    )
    target_type = models.CharField(max_length=30, choices=ReportTargetType.choices)
    target_id = models.UUIDField()
    reason = models.CharField(max_length=80)
    priority = models.SmallIntegerField(
        choices=ReportPriority.choices, default=ReportPriority.STANDARD
    )
    details = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20, choices=ReportStatus.choices, default=ReportStatus.OPEN
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "reports"
        indexes = [
            models.Index(fields=["status", "priority", "created_at"], name="idx_reports_queue"),
        ]


class ModerationAction(UUIDPrimaryKeyModel):
    """Action journalisée, avec motivation envoyée à la personne concernée (DSA)."""

    class Action(models.TextChoices):
        WARN = "warn"
        REMOVE_CONTENT = "remove_content"
        SUSPEND_ACCOUNT = "suspend_account"
        REINSTATE_ACCOUNT = "reinstate_account"
        DISMISS = "dismiss"
        APPROVE_OPPORTUNITY = "approve_opportunity"
        REJECT_OPPORTUNITY = "reject_opportunity"
        ARBITRATE_CREDIT = "arbitrate_credit"

    report = models.ForeignKey(
        Report, null=True, blank=True, on_delete=models.SET_NULL, related_name="actions"
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="moderation_actions"
    )
    target_type = models.CharField(max_length=30)
    target_id = models.UUIDField()
    affected_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=50, choices=Action.choices)
    statement_of_reasons = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "moderation_actions"


class Appeal(UUIDPrimaryKeyModel):
    action = models.ForeignKey(ModerationAction, on_delete=models.CASCADE, related_name="appeals")
    appellant = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="appeals"
    )
    body = models.TextField()
    status = models.CharField(
        max_length=20, choices=AppealStatus.choices, default=AppealStatus.OPEN
    )
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    decision_reasons = models.TextField(blank=True, default="")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "appeals"


class AuditLog(models.Model):
    """Journal d'audit : lectures de contenu privé par un modérateur, actions admin, exports."""

    id = models.BigAutoField(primary_key=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    action = models.CharField(max_length=80)
    target_type = models.CharField(max_length=30, blank=True, default="")
    target_id = models.UUIDField(null=True, blank=True)
    reason = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        indexes = [models.Index(fields=["actor", "-created_at"], name="idx_audit_actor")]
