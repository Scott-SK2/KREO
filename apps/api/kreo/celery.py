import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "kreo.settings.dev")

app = Celery("kreo")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Tâches planifiées (voir cahier des charges : refus automatiques, rappels, délai médian).
app.conf.beat_schedule = {
    "close-expired-opportunities": {
        "task": "kreo.opportunities.tasks.close_expired_opportunities",
        "schedule": 60 * 15,
    },
    "recompute-response-times": {
        "task": "kreo.applications.tasks.recompute_response_times",
        "schedule": crontab(hour=3, minute=0),
    },
    "remind-unanswered-applications": {
        "task": "kreo.applications.tasks.remind_unanswered_applications",
        "schedule": crontab(hour=9, minute=0),
    },
    "warn-expiring-opportunities": {
        "task": "kreo.opportunities.tasks.warn_expiring_opportunities",
        "schedule": crontab(hour=9, minute=5),
    },
    "purge-deleted-accounts": {
        "task": "kreo.identity.tasks.purge_deleted_accounts",
        "schedule": crontab(hour=4, minute=0),
    },
    "send-daily-digests": {
        "task": "kreo.notifications.tasks.send_daily_digests",
        "schedule": crontab(hour=18, minute=0),
    },
}
