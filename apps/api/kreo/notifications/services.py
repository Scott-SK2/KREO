"""Création idempotente de notifications et routage e-mail selon les préférences."""

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone

from .catalog import spec_for
from .models import Notification, NotificationPreference

logger = logging.getLogger("kreo.notifications")
BRUSSELS = ZoneInfo("Europe/Brussels")


def _preference(user, event_key):
    spec = spec_for(event_key)
    pref = NotificationPreference.objects.filter(user=user, event_key=event_key).first()
    return {
        "in_app": pref.in_app if pref else spec.in_app,
        "email": True if spec.mandatory_email else (pref.email if pref else spec.email),
        "push": (pref.push if pref else spec.push) and settings.FEATURES["push"],
    }


def in_quiet_hours(now: datetime | None = None) -> bool:
    now = (now or timezone.now()).astimezone(BRUSSELS)
    start, end = settings.QUIET_HOURS
    return now.hour >= start or now.hour < end


def notify(
    *,
    event_key: str,
    recipient,
    payload: dict | None = None,
    dedup_key: str | None = None,
    deep_link: str = "",
) -> Notification | None:
    """
    Crée la notification in-app (si activée) et planifie l'e-mail selon le mode du catalogue.
    `dedup_key` garantit l'idempotence : un second appel avec la même clé ne fait rien.
    """
    if recipient is None or recipient.deleted_at is not None:
        return None
    spec = spec_for(event_key)
    prefs = _preference(recipient, event_key)
    payload = payload or {}

    notification = None
    if prefs["in_app"] or prefs["email"]:
        try:
            with transaction.atomic():
                notification = Notification.objects.create(
                    recipient=recipient,
                    event_key=event_key,
                    payload=payload,
                    dedup_key=dedup_key,
                    deep_link=deep_link,
                    read_at=None if prefs["in_app"] else timezone.now(),
                )
        except IntegrityError:
            logger.info("notification deduplicated", extra={"event": event_key})
            return None

    if prefs["email"] and spec.email_mode != "none":
        from .tasks import send_notification_email

        if spec.email_mode == "immediate":
            delay = 0
            if in_quiet_hours() and not spec.ignore_quiet_hours and not spec.mandatory_email:
                delay = _seconds_until_morning()
            send_notification_email.apply_async(args=[str(notification.id)], countdown=delay)
        elif spec.email_mode == "if_unread_1h":
            send_notification_email.apply_async(args=[str(notification.id)], countdown=3600)
        # digest : traité par send_daily_digests
    return notification


def _seconds_until_morning() -> int:
    now = timezone.now().astimezone(BRUSSELS)
    _, end = settings.QUIET_HOURS
    morning = now.replace(hour=end, minute=0, second=0, microsecond=0)
    if morning <= now:
        from datetime import timedelta

        morning += timedelta(days=1)
    return int((morning - now).total_seconds())


def mark_read(user, ids: list | None = None) -> int:
    qs = Notification.objects.filter(recipient=user, read_at__isnull=True)
    if ids:
        qs = qs.filter(id__in=ids)
    return qs.update(read_at=timezone.now())
