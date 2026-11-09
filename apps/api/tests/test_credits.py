import pytest
from django.core import mail

from kreo.credits.models import ProjectCredit
from kreo.identity.models import BetaInvitation
from kreo.projects.services import transition_project

pytestmark = pytest.mark.django_db


def _complete(project, owner):
    transition_project(project=project, target="active", actor=owner)
    return transition_project(project=project, target="completed", actor=owner)


def test_credit_only_after_completion_and_confirmed_by_beneficiary(
    api, project, owner, candidate, other
):
    api.force_authenticate(owner)
    url = f"/api/v1/projects/{project.id}/credits"
    resp = api.post(url, {"role_name": "Comédienne", "user_id": str(candidate.id)}, format="json")
    assert resp.status_code == 422 and resp.json()["type"].endswith("project-not-completed")
    _complete(project, owner)
    resp = api.post(url, {"role_name": "Comédienne", "user_id": str(candidate.id)}, format="json")
    assert resp.status_code == 201
    credit_id = resp.json()["id"]
    assert candidate.notifications.filter(event_key="credit.proposed").count() == 1
    # Le porteur ne confirme pas à la place du bénéficiaire
    assert (
        api.post(f"/api/v1/credits/{credit_id}/transition", {"status": "confirmed"}).status_code
        == 409
    )
    # Non confirmé : invisible publiquement
    api.force_authenticate(None)
    assert api.get(url).json() == []
    # Le bénéficiaire confirme
    api.force_authenticate(candidate)
    assert (
        api.post(f"/api/v1/credits/{credit_id}/transition", {"status": "confirmed"}).status_code
        == 200
    )
    api.force_authenticate(None)
    assert api.get(url).json()[0]["role_name"] == "Comédienne"
    assert (
        api.get(f"/api/v1/profiles/{candidate.profile.slug}/credits").json()[0]["project_title"]
        == project.title
    )


def test_dispute_requires_reason_and_never_shows_as_confirmed(
    api, project, owner, candidate, moderator
):
    _complete(project, owner)
    api.force_authenticate(owner)
    credit_id = api.post(
        f"/api/v1/projects/{project.id}/credits",
        {"role_name": "Régie", "user_id": str(candidate.id)},
        format="json",
    ).json()["id"]
    api.force_authenticate(candidate)
    assert (
        api.post(f"/api/v1/credits/{credit_id}/transition", {"status": "disputed"}).status_code
        == 422
    )
    assert (
        api.post(
            f"/api/v1/credits/{credit_id}/transition",
            {"status": "disputed", "reason": "Je n'étais pas à la régie mais au son."},
        ).status_code
        == 200
    )
    api.force_authenticate(None)
    assert api.get(f"/api/v1/projects/{project.id}/credits").json() == []
    # Le porteur corrige et repropose ; ou un modérateur arbitre
    api.force_authenticate(moderator)
    assert (
        api.post(
            f"/api/v1/credits/{credit_id}/transition",
            {"status": "declined", "reason": "Arbitrage : désaccord sur le rôle."},
        ).status_code
        == 200
    )
    assert ProjectCredit.objects.get(id=credit_id).status == "declined"


def test_credit_to_unregistered_email_activates_at_signup(api, project, owner):
    _complete(project, owner)
    api.force_authenticate(owner)
    resp = api.post(
        f"/api/v1/projects/{project.id}/credits",
        {"role_name": "Montage", "email": "future@example.com"},
        format="json",
    )
    assert resp.status_code == 201
    assert any("future@example.com" in m.to for m in mail.outbox)
    # Inscription puis vérification de l'e-mail
    api.force_authenticate(None)
    inv = BetaInvitation.objects.create(inviter=owner)
    api.post(
        "/api/v1/auth/register",
        {
            "email": "future@example.com",
            "password": "MotDePasse-Solide-42",
            "birth_date": "1990-01-01",
            "terms_version": "2026-11",
            "invitation_code": inv.code,
        },
    )
    token = (
        [m for m in mail.outbox if "verifier-email" in m.body][0].body.split("token=")[1].split()[0]
    )
    api.post("/api/v1/auth/verify-email", {"token": token})
    credit = ProjectCredit.objects.get(role_name="Montage")
    assert (
        credit.user is not None
        and credit.user.email == "future@example.com"
        and credit.invited_email == ""
    )
