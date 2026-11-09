import statistics
from datetime import timedelta

from celery import shared_task
from django.db.models import F
from django.utils import timezone


@shared_task
def recompute_response_times():
    """Délai médian de première réponse de chaque porteur (90 derniers jours)."""
    from kreo.identity.models import User

    from .models import Application, OwnerResponseStat

    since = timezone.now() - timedelta(days=90)
    owners = User.objects.filter(projects_owned__isnull=False).distinct()
    for owner in owners.iterator():
        delays = [
            (a.first_response_at - a.submitted_at).total_seconds() / 3600
            for a in Application.objects.filter(
                role__opportunity__project__owner=owner,
                first_response_at__isnull=False,
                submitted_at__gte=since,
            ).only("first_response_at", "submitted_at")
        ]
        OwnerResponseStat.objects.update_or_create(
            user=owner,
            defaults={
                "median_hours": round(statistics.median(delays), 1) if delays else None,
                "sample_size": len(delays),
            },
        )
    return owners.count()


@shared_task
def remind_unanswered_applications():
    """Rappel au porteur : candidatures sans réponse depuis 5 jours (une fois par candidature)."""
    from kreo.notifications.services import notify

    from .models import Application

    limit = timezone.now() - timedelta(days=5)
    qs = Application.objects.filter(status="submitted", submitted_at__lt=limit).select_related(
        "role__opportunity__project__owner"
    )
    by_owner = {}
    for app in qs:
        by_owner.setdefault(app.role.opportunity.project.owner, []).append(app)
    for owner, apps in by_owner.items():
        notify(
            event_key="applications.reminder_5d",
            recipient=owner,
            payload={
                "title": f"{len(apps)} candidature(s) attendent ta réponse depuis 5 jours",
                "count": len(apps),
            },
            dedup_key=f"applications.reminder_5d:{owner.id}:{timezone.now():%Y-%m-%d}",
            deep_link="/tableau-de-bord/candidats",
        )
    return len(by_owner)


@shared_task
def notify_saved_search_matches(opportunity_id: str):
    """Phase L : une seule notification par annonce et par recherche sauvegardée."""
    from django.conf import settings

    if not settings.FEATURES["saved_searches"]:
        return 0
    from kreo.notifications.services import notify
    from kreo.opportunities.filters import search_opportunities

    from .models import SavedSearch

    sent = 0
    for saved in SavedSearch.objects.filter(alerts_enabled=True).select_related("user"):
        if search_opportunities(saved.filters, saved.user).filter(id=opportunity_id).exists():
            notify(
                event_key="saved_search.match",
                recipient=saved.user,
                payload={
                    "title": "Nouvelle annonce correspondant à ta recherche",
                    "saved_search_id": str(saved.id),
                },
                dedup_key=f"saved_search.match:{saved.id}:{opportunity_id}",
                deep_link=f"/annonces/{opportunity_id}",
            )
            SavedSearch.objects.filter(pk=saved.pk).update(last_notified_at=timezone.now())
            sent += 1
    return sent


__all__ = [
    "recompute_response_times",
    "remind_unanswered_applications",
    "notify_saved_search_matches",
    "F",
]
