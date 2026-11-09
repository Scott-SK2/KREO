import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .catalog import spec_for

logger = logging.getLogger("kreo.notifications")


def _render(notification) -> tuple[str, str]:
    spec = spec_for(notification.event_key)
    title = notification.payload.get("title") or spec.title_fr
    body_lines = [title, ""]
    if notification.payload.get("body"):
        body_lines += [notification.payload["body"], ""]
    if notification.deep_link:
        body_lines += [f"{settings.SITE_URL}{notification.deep_link}", ""]
    body_lines += ["— L'équipe KREO", "Une idée, des talents, un projet."]
    return f"{title} — KREO", "\n".join(body_lines)


@shared_task
def send_notification_email(notification_id: str):
    from .models import Notification

    notification = (
        Notification.objects.select_related("recipient").filter(id=notification_id).first()
    )
    if notification is None or notification.email_sent_at:
        return
    spec = spec_for(notification.event_key)
    if spec.email_mode == "if_unread_1h" and notification.read_at is not None:
        return
    recipient = notification.recipient
    if recipient.deleted_at:
        return
    # Maximum 1 e-mail non transactionnel par jour et par membre.
    if not spec.mandatory_email and spec.email_mode != "if_unread_1h":
        since = timezone.now() - timedelta(days=1)
        already = (
            Notification.objects.filter(recipient=recipient, email_sent_at__gte=since)
            .exclude(event_key__in=[k for k, s in _mandatory_keys()])
            .exists()
        )
        if already:
            return
    subject, body = _render(notification)
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [recipient.email])
    notification.email_sent_at = timezone.now()
    notification.save(update_fields=["email_sent_at"])


def _mandatory_keys():
    from .catalog import CATALOG

    return [(k, s) for k, s in CATALOG.items() if s.mandatory_email]


@shared_task
def send_daily_digests():
    """Résumé quotidien des événements en mode digest (nouvelles candidatures)."""
    from kreo.identity.models import User

    from .catalog import CATALOG
    from .models import Notification

    digest_keys = [k for k, s in CATALOG.items() if s.email_mode == "digest"]
    since = timezone.now() - timedelta(days=1)
    pending = Notification.objects.filter(
        event_key__in=digest_keys, email_sent_at__isnull=True, created_at__gte=since
    )
    sent = 0
    for user_id in pending.values_list("recipient_id", flat=True).distinct():
        user = User.objects.filter(id=user_id, deleted_at__isnull=True).first()
        if not user:
            continue
        items = list(pending.filter(recipient_id=user_id))
        lines = [f"Tu as {len(items)} nouvelle(s) candidature(s) aujourd'hui.", ""]
        for n in items:
            lines.append(f"• {n.payload.get('title', spec_for(n.event_key).title_fr)}")
        lines += ["", f"{settings.SITE_URL}/tableau-de-bord/candidats", "", "— L'équipe KREO"]
        send_mail(
            "Ton résumé KREO du jour", "\n".join(lines), settings.DEFAULT_FROM_EMAIL, [user.email]
        )
        pending.filter(recipient_id=user_id).update(email_sent_at=timezone.now())
        sent += 1
    return sent
