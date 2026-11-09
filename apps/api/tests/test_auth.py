from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from kreo.common.utils import hash_token
from kreo.identity.models import BetaInvitation, OneTimeToken, User

pytestmark = pytest.mark.django_db

REGISTER = "/api/v1/auth/register"
PAYLOAD = {
    "email": "nouveau@example.com",
    "password": "MotDePasse-Solide-42",
    "birth_date": "1995-06-01",
    "terms_version": "2026-11",
}


def test_register_with_valid_invitation_sends_verification(api, invitation):
    resp = api.post(REGISTER, {**PAYLOAD, "invitation_code": invitation.code.lower()})
    assert resp.status_code == 201, resp.content
    user = User.objects.get(email="nouveau@example.com")
    assert not user.is_email_verified
    invitation.refresh_from_db()
    assert invitation.used_by == user
    # 5 invitations à partager
    assert BetaInvitation.objects.filter(inviter=user).count() == 5
    assert len(mail.outbox) == 1 and "verifier-email?token=" in mail.outbox[0].body


def test_register_rejects_used_or_expired_or_unknown_code(api, invitation, other):
    invitation.used_at = timezone.now()
    invitation.used_by = other
    invitation.save()
    resp = api.post(REGISTER, {**PAYLOAD, "invitation_code": invitation.code})
    assert resp.status_code == 422
    assert resp["Content-Type"] == "application/problem+json"
    assert resp.json()["type"].endswith("invitation-invalid")

    expired = BetaInvitation.objects.create(expires_at=timezone.now() - timedelta(days=1))
    assert api.post(REGISTER, {**PAYLOAD, "invitation_code": expired.code}).status_code == 422
    assert api.post(REGISTER, {**PAYLOAD, "invitation_code": "NOPE1234"}).status_code == 422


def test_register_requires_18(api, invitation):
    young = (timezone.localdate() - timedelta(days=365 * 17)).isoformat()
    resp = api.post(REGISTER, {**PAYLOAD, "birth_date": young, "invitation_code": invitation.code})
    assert resp.status_code == 422
    assert resp.json()["type"].endswith("minimum-age")


def test_verify_email_then_login_sets_cookies(api, invitation):
    api.post(REGISTER, {**PAYLOAD, "invitation_code": invitation.code})
    token = mail.outbox[0].body.split("token=")[1].split()[0]
    # Connexion refusée avant vérification
    resp = api.post(
        "/api/v1/auth/login", {"email": PAYLOAD["email"], "password": PAYLOAD["password"]}
    )
    assert resp.status_code == 401
    resp = api.post("/api/v1/auth/verify-email", {"token": token})
    assert resp.status_code == 200, resp.content
    assert "kreo_access" in resp.cookies and "kreo_refresh" in resp.cookies
    assert resp.cookies["kreo_access"]["httponly"]
    # Le lien est à usage unique
    assert api.post("/api/v1/auth/verify-email", {"token": token}).status_code == 422
    # /me avec le cookie
    api.cookies = resp.cookies
    me = api.get("/api/v1/me")
    assert me.status_code == 200 and me.json()["email_verified"] is True


def test_verification_link_expires_after_24h(api, invitation):
    api.post(REGISTER, {**PAYLOAD, "invitation_code": invitation.code})
    token = mail.outbox[0].body.split("token=")[1].split()[0]
    OneTimeToken.objects.filter(token_hash=hash_token(token)).update(
        expires_at=timezone.now() - timedelta(minutes=1)
    )
    assert api.post("/api/v1/auth/verify-email", {"token": token}).status_code == 422


def test_login_lockout_after_5_failures(api, owner):
    for _ in range(5):
        assert (
            api.post("/api/v1/auth/login", {"email": owner.email, "password": "faux"}).status_code
            == 401
        )
    owner.refresh_from_db()
    assert owner.is_locked
    resp = api.post(
        "/api/v1/auth/login", {"email": owner.email, "password": "MotDePasse-Solide-42"}
    )
    assert resp.status_code == 401
    assert "tentatives" in resp.json()["detail"].lower()


def test_mobile_client_receives_tokens_and_logout_all_devices(api, owner):
    resp = api.post(
        "/api/v1/auth/login",
        {"email": owner.email, "password": "MotDePasse-Solide-42"},
        HTTP_X_CLIENT="mobile",
    )
    assert resp.status_code == 200
    access = resp.json()["access"]
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
    assert api.get("/api/v1/me").status_code == 200
    assert api.post("/api/v1/auth/logout", {"all_devices": True}).status_code == 204
    # Le même jeton est révoqué partout
    assert api.get("/api/v1/me").status_code == 401


def test_password_reset_flow(api, owner):
    assert api.post("/api/v1/auth/password-reset", {"email": owner.email}).status_code == 202
    assert (
        api.post("/api/v1/auth/password-reset", {"email": "inconnu@example.com"}).status_code == 202
    )
    token = mail.outbox[0].body.split("token=")[1].split()[0]
    resp = api.post(
        "/api/v1/auth/password-reset/confirm",
        {"token": token, "password": "Nouveau-Mot-De-Passe-7"},
    )
    assert resp.status_code == 204
    assert (
        api.post(
            "/api/v1/auth/login", {"email": owner.email, "password": "Nouveau-Mot-De-Passe-7"}
        ).status_code
        == 200
    )


def test_phone_verification_marks_owner_verified(api, candidate):
    api.force_authenticate(candidate)
    resp = api.post("/api/v1/auth/phone/verify", {"phone_number": "+32470000000"})
    assert resp.status_code == 202 and "debug_code" in resp.json()
    assert api.post("/api/v1/auth/phone/verify", {"code": "000000"}).status_code in (422, 200)
    resp = api.post("/api/v1/auth/phone/verify", {"code": resp.json()["debug_code"]})
    assert resp.status_code == 200 and resp.json()["phone_verified"] is True


def test_delete_account_anonymises_immediately(api, candidate):
    api.force_authenticate(candidate)
    assert api.delete("/api/v1/me").status_code == 204
    candidate.refresh_from_db()
    assert candidate.status == "deleted" and candidate.email.startswith("deleted+")
    assert candidate.profile.display_name == "Compte supprimé"


def test_export_returns_json(api, candidate):
    api.force_authenticate(candidate)
    resp = api.get("/api/v1/me/export")
    assert resp.status_code == 200
    assert resp.json()["account"]["email"] == candidate.email


def test_problem_json_on_404_and_401(api):
    resp = api.get("/api/v1/me")
    assert resp.status_code == 401 and resp["Content-Type"] == "application/problem+json"
    resp = api.get("/api/v1/profiles/inexistant")
    assert resp.status_code == 404 and resp.json()["title"] == "Ressource introuvable"
