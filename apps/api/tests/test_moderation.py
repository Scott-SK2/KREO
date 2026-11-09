import pytest

from kreo.moderation.models import AuditLog, Report

pytestmark = pytest.mark.django_db


def test_report_priority_queue_and_action_with_statement(
    api, open_opportunity, owner, candidate, moderator, other
):
    api.force_authenticate(candidate)
    assert (
        api.post(
            "/api/v1/reports",
            {"target_type": "opportunity", "target_id": str(open_opportunity.id), "reason": "spam"},
        ).status_code
        == 201
    )
    api.force_authenticate(other)
    resp = api.post(
        "/api/v1/reports",
        {
            "target_type": "user",
            "target_id": str(owner.id),
            "reason": "threats",
            "details": "Menaces en message privé.",
        },
    )
    assert resp.status_code == 201 and resp.json()["priority"] == 1
    # Le membre ne voit pas la file
    assert api.get("/api/v1/admin/reports").status_code == 403

    api.force_authenticate(moderator)
    queue = api.get("/api/v1/admin/reports").json()["results"]
    assert [r["reason"] for r in queue] == ["threats", "spam"]  # sécurité des personnes d'abord
    safety_report = queue[0]["id"]
    # Motivation trop courte refusée
    assert (
        api.post(
            f"/api/v1/admin/reports/{safety_report}/actions",
            {"action": "suspend_account", "statement_of_reasons": "court"},
        ).status_code
        == 400
    )
    resp = api.post(
        f"/api/v1/admin/reports/{safety_report}/actions",
        {
            "action": "suspend_account",
            "statement_of_reasons": "Menaces répétées envers un membre, contraires à la charte.",
        },
    )
    assert resp.status_code == 201
    owner.refresh_from_db()
    assert owner.status == "suspended"
    assert Report.objects.get(id=safety_report).status == "actioned"
    # Motivation envoyée à la personne concernée (e-mail obligatoire)
    assert owner.notifications.filter(event_key="moderation.decision").count() == 1
    assert AuditLog.objects.filter(actor=moderator, action="moderation.suspend_account").exists()
    # Un compte suspendu lit mais ne publie plus
    api.force_authenticate(owner)
    assert (
        api.get("/api/v1/me/moderation-decisions")
        .json()["results"][0]["statement_of_reasons"]
        .startswith("Menaces")
    )
    assert (
        api.post(
            f"/api/v1/projects/{open_opportunity.project.id}/updates", {"body": "x"}, format="json"
        ).status_code
        == 403
    )


def test_moderator_reading_private_content_is_audited(
    api, open_opportunity, owner, candidate, moderator
):
    role = open_opportunity.roles.first()
    api.force_authenticate(candidate)
    app_id = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    api.force_authenticate(moderator)
    assert (
        api.get(
            f"/api/v1/applications/{app_id}", HTTP_X_MODERATION_REASON="signalement #12"
        ).status_code
        == 200
    )
    log = AuditLog.objects.get(action="moderation.read_application")
    assert log.reason == "signalement #12" and str(log.target_id) == app_id
    # Le modérateur ne voit que ses propres actions dans le journal
    assert (
        api.get("/api/v1/admin/audit").json()["results"][0]["action"]
        == "moderation.read_application"
    )


def test_appeals_are_phase_l_feature_flag(api, candidate, settings):
    api.force_authenticate(candidate)
    import uuid

    resp = api.post(
        "/api/v1/appeals",
        {"action_id": str(uuid.uuid4()), "body": "Je conteste cette décision pour ces raisons."},
    )
    assert resp.status_code == 404  # action inexistante
    resp = api.post(
        "/api/v1/me/favorites", {"target_type": "project", "target_id": str(uuid.uuid4())}
    )
    assert resp.status_code == 422 and resp.json()["type"].endswith("feature-disabled")
