from django.conf import settings
from django.db import models

from kreo.common.choices import DevicePlatform
from kreo.common.models import UUIDPrimaryKeyModel


class Notification(UUIDPrimaryKeyModel):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_key = models.CharField(max_length=80)
    payload = models.JSONField(default=dict, blank=True)
    dedup_key = models.CharField(max_length=180, unique=True, null=True, blank=True)
    deep_link = models.CharField(max_length=300, blank=True, default="")
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications"
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"], name="idx_notifs_recipient"
            )
        ]


class NotificationPreference(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences"
    )
    event_key = models.CharField(max_length=80)
    in_app = models.BooleanField(default=True)
    email = models.BooleanField(default=True)
    push = models.BooleanField(default=False)

    class Meta:
        db_table = "notification_preferences"
        constraints = [models.UniqueConstraint(fields=["user", "event_key"], name="uq_notif_pref")]


class DeviceToken(UUIDPrimaryKeyModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="device_tokens"
    )
    platform = models.CharField(max_length=12, choices=DevicePlatform.choices)
    push_token = models.TextField(unique=True)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "device_tokens"
