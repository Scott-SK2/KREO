import pytest

pytestmark = pytest.mark.django_db


def test_conversation_scoped_to_application_and_block_cuts_it(
    api, open_opportunity, owner, candidate, other
):
    role = open_opportunity.roles.first()
    api.force_authenticate(candidate)
    app_id = api.post(f"/api/v1/roles/{role.id}/applications", {}, format="json").json()["id"]
    # Un tiers ne peut pas ouvrir la conversation
    api.force_authenticate(other)
    assert (
        api.post("/api/v1/conversations", {"application_id": app_id}, format="json").status_code
        == 422
    )
    # Le porteur écrit au candidat ; conseils de sécurité fournis
    api.force_authenticate(owner)
    resp = api.post("/api/v1/conversations", {"application_id": app_id}, format="json")
    assert resp.status_code == 201
    conv_id = resp.json()["id"]
    assert len(resp.json()["safety_tips"]) == 3
    assert (
        api.post(
            f"/api/v1/conversations/{conv_id}/messages", {"body": "Bonjour, dispo mardi ?"}
        ).status_code
        == 201
    )
    assert api.post(f"/api/v1/conversations/{conv_id}/messages", {"body": "   "}).status_code == 400
    # Le candidat voit 1 non-lu, lit, puis 0
    api.force_authenticate(candidate)
    convs = api.get("/api/v1/conversations").json()
    assert convs[0]["unread_count"] == 1
    assert api.post(f"/api/v1/conversations/{conv_id}/read").status_code == 204
    assert api.get("/api/v1/conversations").json()[0]["unread_count"] == 0
    assert (
        candidate.notifications.filter(event_key="message.new", read_at__isnull=False).count() == 1
    )
    # Un tiers ne lit pas
    api.force_authenticate(other)
    assert api.get(f"/api/v1/conversations/{conv_id}/messages").status_code == 404
    # Blocage : la conversation est coupée
    api.force_authenticate(candidate)
    api.post("/api/v1/blocks", {"user_id": str(owner.id)})
    api.force_authenticate(owner)
    resp = api.post(f"/api/v1/conversations/{conv_id}/messages", {"body": "Encore là ?"})
    assert resp.status_code == 422 and resp.json()["type"].endswith("blocked")
