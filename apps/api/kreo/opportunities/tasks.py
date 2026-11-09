import logging
from datetime import timedelta

from celery import shared_task
from django.db.models import Max, Q
from django.utils import timezone

logger = logging.getLogger("kreo.opportunities")


@shared_task
def close_expired_opportunities():
    """Ferme les annonces dont tous les rôles ont dépassé leur échéance."""
    from kreo.common.choices import OpportunityStatus, RoleStatus

    from .models import Opportunity, OpportunityRole
    from .services import transition_opportunity

    now = timezone.now()
    OpportunityRole.objects.filter(status=RoleStatus.OPEN, deadline_at__lt=now).update(
        status=RoleStatus.CLOSED
    )
    closed = 0
    for opportunity in (
        Opportunity.objects.filter(status=OpportunityStatus.OPEN)
        .exclude(roles__status=RoleStatus.OPEN)
        .distinct()
    ):
        transition_opportunity(
            opportunity=opportunity, target=OpportunityStatus.CLOSED, actor=None, system=True
        )
        closed += 1
    return closed


@shared_task
def warn_expiring_opportunities():
    """J-2 : prévient le porteur qu'une annonce expire bientôt (une seule fois)."""
    from kreo.notifications.services import notify

    from .models import Opportunity

    now = timezone.now()
    window = (
        now + timedelta(days=2) - timedelta(hours=12),
        now + timedelta(days=2) + timedelta(hours=12),
    )
    qs = (
        Opportunity.objects.filter(status="open")
        .annotate(last_deadline=Max("roles__deadline_at"))
        .filter(Q(last_deadline__range=window))
        .select_related("created_by", "project")
    )
    for opportunity in qs:
        notify(
            event_key="opportunity.expiring_2d",
            recipient=opportunity.created_by,
            payload={
                "title": f"« {opportunity.title} » expire dans 2 jours",
                "opportunity_id": str(opportunity.id),
            },
            dedup_key=f"opportunity.expiring_2d:{opportunity.id}",
            deep_link=f"/annonces/{opportunity.id}",
        )
    return qs.count()
