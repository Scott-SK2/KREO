import pytest

from kreo.applications.models import Application
from kreo.notifications.models import Notification
from kreo.projects.models import ProjectMember

pytestmark = pytest.mark.django_db


def _role(open_opportunity, title):
    return open_opportunity.roles.get(title=title)


def test_apply_once_per_role_and_not_own_project(api, open_opportunity, owner, candidate):
    role = _role(open_opportunity, "Comédien·ne principal·e")
    api.force_authenticate(owner)
    assert api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").status_code == 422
    api.force_authenticate(candidate)
    resp = api.post(
        f"/api/v1/roles/{role.id}/applications",
        {"message": "Très motivé·e", "availability_confirmed": True},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert resp.json()["status"] == "submitted"
    assert resp.json()["allowed_transitions"] == ["withdrawn"]
    resp = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json")
    assert resp.status_code == 409 and resp.json()["type"].endswith("already-applied")
    # Le porteur est notifié une seule fois
    assert Notification.objects.filter(recipient=owner, event_key="application.new").count() == 1


def test_candidate_sees_history_and_cannot_be_seen_by_others(
    api, open_opportunity, owner, candidate, other
):
    role = _role(open_opportunity, "Comédien·ne principal·e")
    api.force_authenticate(candidate)
    app_id = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    api.force_authenticate(other)
    assert api.get(f"/api/v1/applications/{app_id}").status_code == 404
    assert api.get(f"/api/v1/roles/{role.id}/applications").status_code == 422
    # Le porteur ouvre → « viewed » automatique, tracé
    api.force_authenticate(owner)
    resp = api.get(f"/api/v1/applications/{app_id}")
    assert resp.json()["status"] == "viewed"
    events = api.get(f"/api/v1/applications/{app_id}/events").json()
    assert [e["to_status"] for e in events] == ["submitted", "viewed"]
    assert events[1]["actor"]["display_name"] == "Camille Porteur"
    # Le candidat voit chaque changement avec sa date
    api.force_authenticate(candidate)
    assert all(e["created_at"] for e in api.get(f"/api/v1/applications/{app_id}/events").json())


def test_offer_acceptance_creates_member_and_fills_role(
    api, open_opportunity, owner, candidate, other
):
    role = _role(open_opportunity, "Comédien·ne principal·e")  # 1 place
    api.force_authenticate(candidate)
    app1 = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    api.force_authenticate(other)
    app2 = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]

    api.force_authenticate(owner)
    # Le porteur ne peut pas forcer « accepted »
    assert (
        api.post(f"/api/v1/applications/{app1}/transition", {"status": "accepted"}).status_code
        == 409
    )
    assert (
        api.post(f"/api/v1/applications/{app1}/transition", {"status": "shortlisted"}).status_code
        == 200
    )
    assert (
        api.post(f"/api/v1/applications/{app1}/transition", {"status": "offered"}).status_code
        == 200
    )
    # Plus de place libre pour une seconde offre
    resp = api.post(f"/api/v1/applications/{app2}/transition", {"status": "offered"})
    assert resp.status_code == 409 and resp.json()["type"].endswith("role-full")

    api.force_authenticate(candidate)
    resp = api.post(f"/api/v1/applications/{app1}/transition", {"status": "accepted"})
    assert resp.status_code == 200
    assert ProjectMember.objects.filter(
        project=open_opportunity.project, user=candidate, role="member"
    ).exists()
    role.refresh_from_db()
    assert role.status == "filled"
    # L'autre candidature a reçu un refus courtois automatique, une seule fois
    app2_obj = Application.objects.get(id=app2)
    assert app2_obj.status == "rejected"
    assert (
        Notification.objects.filter(recipient=other, event_key="application.rejected").count() == 1
    )
    # Le rôle plein ne reçoit plus de candidature
    api.force_authenticate(other)
    resp = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json")
    assert resp.status_code == 422 and resp.json()["type"].endswith("role-closed")


def test_closing_opportunity_auto_rejects_everyone_once(
    api, open_opportunity, owner, candidate, other
):
    role = _role(open_opportunity, "Assistant·e plateau")
    api.force_authenticate(candidate)
    api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json")
    api.force_authenticate(other)
    api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json")
    api.force_authenticate(owner)
    assert (
        api.post(
            f"/api/v1/opportunities/{open_opportunity.id}/transition", {"status": "closed"}
        ).status_code
        == 200
    )
    assert Application.objects.filter(role=role, status="rejected").count() == 2
    assert Notification.objects.filter(event_key="application.rejected").count() == 2
    # Métrique : 0 candidature sans réponse à la clôture
    assert not Application.objects.filter(role=role, status="submitted").exists()


def test_withdraw_until_acceptance_and_blocked_user_cannot_apply(
    api, open_opportunity, owner, candidate
):
    role = _role(open_opportunity, "Assistant·e plateau")
    api.force_authenticate(candidate)
    app_id = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    assert (
        api.post(f"/api/v1/applications/{app_id}/transition", {"status": "withdrawn"}).status_code
        == 200
    )
    # Bloqué par le porteur : impossible de postuler ailleurs sur ses projets
    api.force_authenticate(owner)
    api.post("/api/v1/blocks", {"user_id": str(candidate.id)})
    api.force_authenticate(candidate)
    other_role = _role(open_opportunity, "Comédien·ne principal·e")
    resp = api.post(f"/api/v1/roles/{other_role.id}/applications", {}, format="json")
    assert resp.status_code == 422 and resp.json()["type"].endswith("blocked")


def test_coorganiser_manages_inbox(api, open_opportunity, owner, coorga, candidate):
    ProjectMember.objects.create(project=open_opportunity.project, user=coorga, role="manager")
    role = _role(open_opportunity, "Assistant·e plateau")
    api.force_authenticate(candidate)
    app_id = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    api.force_authenticate(coorga)
    inbox = api.get("/api/v1/me/inbox").json()
    assert [a["id"] for a in inbox] == [app_id]
    assert (
        api.post(f"/api/v1/applications/{app_id}/transition", {"status": "shortlisted"}).status_code
        == 200
    )
