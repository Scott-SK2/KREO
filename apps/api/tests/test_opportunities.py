import pytest

from kreo.opportunities.models import Opportunity

pytestmark = pytest.mark.django_db


def _roles(open_opportunity):
    return {r.title: r for r in open_opportunity.roles.all()}


def test_publication_makes_project_visible_and_search_finds_accents(api, open_opportunity, project):
    project.refresh_from_db()
    assert project.status == "preparing"
    resp = api.get("/api/v1/opportunities?q=theatre")
    assert resp.status_code == 200
    assert [o["id"] for o in resp.json()["results"]] == [str(open_opportunity.id)]
    assert api.get("/api/v1/opportunities?q=théâtre").json()["results"]
    assert api.get("/api/v1/opportunities?compensation=paid").json()["results"]
    assert api.get("/api/v1/opportunities?beginner_friendly=true").json()["results"]
    assert api.get("/api/v1/opportunities?discipline=spectacle-vivant").json()["results"]
    assert api.get("/api/v1/opportunities?discipline=musique").json()["results"] == []
    assert api.get("/api/v1/opportunities?q=xylophone").json()["results"] == []
    # Le texte libre couvre aussi les rôles : titre du rôle et discipline du rôle
    assert api.get("/api/v1/opportunities?q=comedien").json()["results"]
    assert api.get("/api/v1/opportunities?q=Théatre").json()["results"]
    assert api.get("/api/v1/opportunities?q=spectacle vivant").json()["results"]


def test_volunteer_role_refused_on_commercial_project(api, project, owner):
    project.is_commercial = True
    project.save()
    api.force_authenticate(owner)
    resp = api.post(
        f"/api/v1/projects/{project.id}/opportunities",
        {
            "title": "Pub",
            "description": "Tournage publicitaire",
            "roles": [{"title": "Figurant", "compensation": "volunteer"}],
        },
        format="json",
    )
    assert resp.status_code == 422 and resp.json()["type"].endswith("volunteer-on-commercial")


def test_forbidden_casting_criteria_refused(api, project, owner):
    api.force_authenticate(owner)
    resp = api.post(
        f"/api/v1/projects/{project.id}/opportunities",
        {
            "title": "Casting",
            "description": "x",
            "roles": [{"title": "Rôle", "compensation": "paid", "requirements": {"religion": "x"}}],
        },
        format="json",
    )
    assert resp.status_code == 422 and resp.json()["type"].endswith("forbidden-criteria")


def test_intimate_scene_requires_moderation_before_publication(api, project, owner, moderator):
    api.force_authenticate(owner)
    resp = api.post(
        f"/api/v1/projects/{project.id}/opportunities",
        {
            "title": "Scène intime",
            "description": "Dit clairement",
            "has_intimate_scene": True,
            "roles": [{"title": "Rôle", "compensation": "paid"}],
        },
        format="json",
    )
    opp_id = resp.json()["id"]
    resp = api.post(f"/api/v1/opportunities/{opp_id}/transition", {"status": "open"})
    assert resp.status_code == 422 and resp.json()["type"].endswith("moderation-pending")

    api.force_authenticate(moderator)
    assert len(api.get("/api/v1/admin/opportunities/pending").json()) == 1
    # Le modérateur approuve via une action hors signalement (admin/users n'est pas le bon endpoint) :
    from kreo.moderation.services import take_action

    take_action(
        moderator=moderator,
        report=None,
        target_type="opportunity",
        target_id=opp_id,
        action="approve_opportunity",
        statement_of_reasons="Annonce conforme : scène intime annoncée clairement.",
    )
    api.force_authenticate(owner)
    assert (
        api.post(f"/api/v1/opportunities/{opp_id}/transition", {"status": "open"}).status_code
        == 200
    )


def test_daily_quota_and_transitions(api, open_opportunity, owner, candidate):
    api.force_authenticate(candidate)
    # Un simple membre ne gère pas l'annonce
    assert (
        api.post(
            f"/api/v1/opportunities/{open_opportunity.id}/transition", {"status": "closed"}
        ).status_code
        == 409
    )
    api.force_authenticate(owner)
    assert (
        api.post(
            f"/api/v1/opportunities/{open_opportunity.id}/transition", {"status": "draft"}
        ).status_code
        == 409
    )
    assert (
        api.post(
            f"/api/v1/opportunities/{open_opportunity.id}/transition", {"status": "closed"}
        ).status_code
        == 200
    )
    assert (
        Opportunity.objects.get(id=open_opportunity.id).roles.filter(status="closed").count() == 2
    )
    # Fermée : plus de candidature, plus de modification
    assert (
        api.patch(
            f"/api/v1/opportunities/{open_opportunity.id}", {"title": "x"}, format="json"
        ).status_code
        == 422
    )
