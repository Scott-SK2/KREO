import logging
from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger("kreo.identity")

EMAIL_SUBJECTS = {
    "email_verification": "Confirme ton adresse e-mail — KREO",
    "password_reset": "Réinitialise ton mot de passe — KREO",
    "account_export_ready": "Ton export de données est prêt — KREO",
    "project_invitation_external": "On t'invite à rejoindre un projet — KREO",
    "credit_proposed_external": "Un crédit t'est proposé sur KREO",
}


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_transactional_email(self, user_id: str, template: str, context: dict):
    from .models import User

    user = User.objects.filter(id=user_id).first()
    if user is None or user.deleted_at:
        return
    body = render_to_string(f"emails/{template}.txt", {**context, "site_url": settings.SITE_URL})
    try:
        send_mail(EMAIL_SUBJECTS[template], body, settings.DEFAULT_FROM_EMAIL, [user.email])
    except Exception as exc:  # pragma: no cover - dépend du fournisseur
        logger.warning("email send failed", extra={"event": template})
        raise self.retry(exc=exc)
    logger.info("email sent", extra={"event": template})


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_external_email(self, to_email: str, template: str, context: dict):
    """E-mail à une adresse non inscrite (invitation de projet, crédit proposé par e-mail)."""
    body = render_to_string(f"emails/{template}.txt", {**context, "site_url": settings.SITE_URL})
    try:
        send_mail(EMAIL_SUBJECTS[template], body, settings.DEFAULT_FROM_EMAIL, [to_email])
    except Exception as exc:  # pragma: no cover
        raise self.retry(exc=exc)


@shared_task
def send_sms_code(user_id: str, phone_number: str, code: str):
    # Fournisseur SMS à brancher en sprint B3 (fiche 13). En dev, le code est journalisé masqué.
    logger.info("sms code issued", extra={"event": "phone_verification"})


@shared_task
def export_or_purge_notice(user_id: str):
    logger.info("account deletion scheduled", extra={"event": "account_deleted"})


@shared_task
def purge_deleted_accounts():
    """Effacement définitif des comptes supprimés depuis plus de 30 jours.
    Le journal de modération et les obligations légales sont conservés (références SET NULL)."""
    from .models import User

    limit = timezone.now() - timedelta(days=settings.ACCOUNT_PURGE_AFTER_DAYS)
    qs = User.objects.filter(deleted_at__lt=limit, status="deleted")
    count = qs.count()
    for user in qs.iterator():
        user.delete()
    logger.info("accounts purged", extra={"event": "accounts_purged", "duration_ms": count})
    return count
