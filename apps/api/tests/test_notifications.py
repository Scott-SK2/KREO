import pytest

from kreo.notifications.models import Notification, NotificationPreference
from kreo.notifications.services import notify

pytestmark = pytest.mark.django_db


def test_dedup_key_makes_notify_idempotent(candidate):
    assert (
        notify(
            event_key="application.offered",
            recipient=candidate,
            payload={"title": "x"},
            dedup_key="k1",
        )
        is not None
    )
    assert (
        notify(
            event_key="application.offered",
            recipient=candidate,
            payload={"title": "x"},
            dedup_key="k1",
        )
        is None
    )
    assert Notification.objects.filter(recipient=candidate).count() == 1


def test_preferences_respect_mandatory_email(api, candidate):
    api.force_authenticate(candidate)
    prefs = api.get("/api/v1/me/notification-preferences").json()
    assert any(p["event_key"] == "moderation.decision" and p["mandatory_email"] for p in prefs)
    resp = api.put(
        "/api/v1/me/notification-preferences",
        [
            {"event_key": "moderation.decision", "email": False},
            {"event_key": "application.viewed", "in_app": False},
        ],
        format="json",
    )
    assert resp.status_code == 200
    assert (
        NotificationPreference.objects.get(user=candidate, event_key="moderation.decision").email
        is True
    )
    assert (
        NotificationPreference.objects.get(user=candidate, event_key="application.viewed").in_app
        is False
    )
    # Désactivé in-app : la notification est créée déjà lue (aucun bruit)
    notify(event_key="application.viewed", recipient=candidate, dedup_key="v1")
    assert api.get("/api/v1/notifications?unread=true").json()["results"] == []
    assert api.post("/api/v1/notifications/read", {}, format="json").status_code == 200
