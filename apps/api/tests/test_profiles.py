import pytest

from kreo.referentials.models import City, Discipline

pytestmark = pytest.mark.django_db


def test_onboarding_requires_two_disciplines_and_hides_private_data(api, candidate):
    api.force_authenticate(candidate)
    theatre = Discipline.objects.get(slug="theatre").id
    danse = Discipline.objects.get(slug="danse").id
    ixelles = City.objects.get(postal_code="1050").id

    resp = api.patch("/api/v1/me/profile", {"discipline_ids": [theatre]}, format="json")
    assert resp.status_code == 400
    assert resp.json()["errors"][0]["field"] == "discipline_ids"

    resp = api.patch(
        "/api/v1/me/profile",
        {
            "display_name": "Alex",
            "discipline_ids": [theatre, danse],
            "city_id": ixelles,
            "attributes": [{"attribute_key": "languages", "value_json": ["fr", "nl"]}],
        },
        format="json",
    )
    assert resp.status_code == 200, resp.content
    body = resp.json()
    assert body["onboarding_completed_at"] is not None
    assert body["completion"]["score"] > 0
    assert "email" not in body

    # Attribut hors liste fermée refusé (RGPD art. 9)
    resp = api.patch(
        "/api/v1/me/profile",
        {"attributes": [{"attribute_key": "religion", "value_json": "x"}]},
        format="json",
    )
    assert resp.status_code == 400

    # Vue publique : attribut privé par défaut masqué, pas de contact
    api.force_authenticate(None)
    public = api.get(f"/api/v1/profiles/{body['slug']}")
    assert public.status_code == 200
    assert public.json()["attributes"] == []
    assert "email" not in public.json() and "phone" not in str(public.json())


def test_video_links_only_youtube_vimeo(api, candidate):
    api.force_authenticate(candidate)
    resp = api.patch(
        "/api/v1/me/profile", {"video_links": ["https://example.com/v"]}, format="json"
    )
    assert resp.status_code == 400
    resp = api.patch(
        "/api/v1/me/profile", {"video_links": ["https://vimeo.com/123"]}, format="json"
    )
    assert resp.status_code == 200
