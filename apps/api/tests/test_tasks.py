from datetime import timedelta

import pytest
from django.utils import timezone

from kreo.applications.models import Application, OwnerResponseStat
from kreo.applications.services import apply, transition_application
from kreo.applications.tasks import recompute_response_times, remind_unanswered_applications
from kreo.notifications.models import Notification
from kreo.opportunities.models import Opportunity
from kreo.opportunities.tasks import close_expired_opportunities, warn_expiring_opportunities

pytestmark = pytest.mark.django_db


def test_expired_roles_close_the_opportunity_and_reject_applicants(open_opportunity, candidate):
    role = open_opportunity.roles.first()
    apply(role=role, applicant=candidate)
    open_opportunity.roles.update(deadline_at=timezone.now() - timedelta(hours=1))
    assert close_expired_opportunities() == 1
    assert Opportunity.objects.get(id=open_opportunity.id).status == "closed"
    assert Application.objects.get(role=role, applicant=candidate).status == "rejected"
    assert (
        Notification.objects.filter(recipient=candidate, event_key="application.rejected").count()
        == 1
    )


def test_median_response_time_is_measured_not_rated(open_opportunity, owner, candidate, other):
    role = open_opportunity.roles.get(title="Assistant·e plateau")
    a1 = apply(role=role, applicant=candidate)
    a2 = apply(role=role, applicant=other)
    Application.objects.filter(id=a1.id).update(submitted_at=timezone.now() - timedelta(hours=10))
    Application.objects.filter(id=a2.id).update(submitted_at=timezone.now() - timedelta(hours=30))
    transition_application(application=a1, target="viewed", actor=owner)
    transition_application(application=a2, target="shortlisted", actor=owner)
    recompute_response_times()
    stat = OwnerResponseStat.objects.get(user=owner)
    assert stat.sample_size == 2 and 19 <= stat.median_hours <= 21


def test_reminder_after_5_days_once_per_day_and_expiry_warning(open_opportunity, owner, candidate):
    role = open_opportunity.roles.first()
    app = apply(role=role, applicant=candidate)
    Application.objects.filter(id=app.id).update(submitted_at=timezone.now() - timedelta(days=6))
    assert remind_unanswered_applications() == 1
    assert remind_unanswered_applications() == 1  # même jour : dédoublonné
    assert (
        Notification.objects.filter(recipient=owner, event_key="applications.reminder_5d").count()
        == 1
    )
    open_opportunity.roles.update(deadline_at=timezone.now() + timedelta(days=2))
    assert warn_expiring_opportunities() == 1
    assert (
        Notification.objects.filter(recipient=owner, event_key="opportunity.expiring_2d").count()
        == 1
    )
