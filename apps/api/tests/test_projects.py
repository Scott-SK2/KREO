import pytest

from kreo.projects.models import ProjectMember
from kreo.referentials.models import Discipline

pytestmark = pytest.mark.django_db


def test_create_project_requires_verified_phone(api, candidate, disciplines):
    api.force_authenticate(candidate)
    resp = api.post(
        "/api/v1/projects",
        {"title": "Projet", "description": "Desc", "discipline_ids": [d.id for d in disciplines]},
        format="json",
    )
    assert resp.status_code == 422 and resp.json()["type"].endswith("phone-not-verified")


def test_owner_creates_project_and_draft_is_hidden(api, owner, candidate, disciplines):
    api.force_authenticate(owner)
    resp = api.post(
        "/api/v1/projects",
        {
            "title": "Pièce « Nuit »",
            "description": "Théâtre",
            "discipline_ids": [disciplines[0].id],
        },
        format="json",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert body["status"] == "draft" and "owner" in body["my_roles"]
    assert set(body["allowed_transitions"]) == {"active", "cancelled", "preparing"}
    assert ProjectMember.objects.filter(project_id=body["id"], role="owner").exists()

    api.force_authenticate(candidate)
    assert api.get(f"/api/v1/projects/{body['slug']}").status_code == 404
    assert api.get("/api/v1/projects").json()["results"] == []


def test_transitions_follow_the_table_and_reject_others(api, project, owner, coorga):
    api.force_authenticate(owner)
    url = f"/api/v1/projects/{project.id}/transition"
    # draft → completed n'existe pas
    resp = api.post(url, {"status": "completed"})
    assert resp.status_code == 409 and resp.json()["type"].endswith("invalid-transition")
    assert api.post(url, {"status": "preparing"}).status_code == 200
    assert api.post(url, {"status": "active"}).status_code == 200
    # Le projet est maintenant public
    api.force_authenticate(None)
    assert api.get(f"/api/v1/projects/{project.slug}").status_code == 200

    # Un co-organisateur ne peut pas terminer (réservé au porteur)
    ProjectMember.objects.create(project=project, user=coorga, role="manager")
    api.force_authenticate(coorga)
    resp = api.post(url, {"status": "completed"})
    assert resp.status_code == 409 and resp.json()["type"].endswith("transition-forbidden")
    api.force_authenticate(owner)
    assert api.post(url, {"status": "completed"}).status_code == 200
    assert api.post(url, {"status": "archived"}).status_code == 200
    # Archivé : lecture seule
    assert (
        api.patch(f"/api/v1/projects/{project.id}", {"title": "X"}, format="json").status_code
        == 422
    )


def test_only_manager_edits_project(api, project, candidate, coorga):
    api.force_authenticate(candidate)
    assert (
        api.patch(f"/api/v1/projects/{project.id}", {"title": "X"}, format="json").status_code
        == 404
    )
    ProjectMember.objects.create(project=project, user=coorga, role="manager")
    api.force_authenticate(coorga)
    resp = api.patch(f"/api/v1/projects/{project.id}", {"title": "Nouveau titre"}, format="json")
    assert resp.status_code == 200 and resp.json()["title"] == "Nouveau titre"


def test_coorganiser_invitation_by_link_and_removal(api, project, owner, coorga, candidate):
    api.force_authenticate(owner)
    resp = api.post(f"/api/v1/projects/{project.id}/invitations", {"role": "manager"})
    assert resp.status_code == 201
    token = resp.json()["link_token"]

    api.force_authenticate(coorga)
    resp = api.post("/api/v1/projects/invitations/accept", {"token": token})
    assert resp.status_code == 200 and resp.json()["role"] == "manager"
    # Un co-orga ne peut pas inviter un autre co-orga
    assert (
        api.post(f"/api/v1/projects/{project.id}/invitations", {"role": "manager"}).status_code
        == 422
    )
    # mais peut inviter un membre par e-mail
    resp = api.post(
        f"/api/v1/projects/{project.id}/invitations", {"role": "member", "email": candidate.email}
    )
    assert resp.status_code == 201
    # Le candidat a reçu une notification in-app (e-mail obligatoire)
    assert candidate.notifications.filter(event_key="project.invitation").count() == 1

    # Retrait immédiat du co-orga par le porteur
    api.force_authenticate(owner)
    assert api.delete(f"/api/v1/projects/{project.id}/members/{coorga.id}").status_code == 204
    assert not ProjectMember.objects.filter(project=project, user=coorga).exists()


def test_project_updates_limited_to_4_photos(api, project, owner):
    api.force_authenticate(owner)
    resp = api.post(
        f"/api/v1/projects/{project.id}/updates",
        {"body": "Premier jour de répétition !", "media_ids": []},
        format="json",
    )
    assert resp.status_code == 201
    import uuid

    resp = api.post(
        f"/api/v1/projects/{project.id}/updates",
        {"body": "Trop de photos", "media_ids": [str(uuid.uuid4()) for _ in range(5)]},
        format="json",
    )
    assert resp.status_code == 400


def test_project_search_french_unaccent(api, project, owner):
    api.force_authenticate(owner)
    api.post(f"/api/v1/projects/{project.id}/transition", {"status": "active"})
    api.force_authenticate(None)
    assert len(api.get("/api/v1/projects?q=lumiere").json()["results"]) == 1
    assert len(api.get("/api/v1/projects?q=hiver").json()["results"]) == 1
    assert len(api.get("/api/v1/projects?q=opera").json()["results"]) == 0
    assert (
        len(
            api.get(
                f"/api/v1/projects?discipline={Discipline.objects.get(slug='theatre').slug}"
            ).json()["results"]
        )
        == 1
    )
