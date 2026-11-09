import pytest

pytestmark = pytest.mark.django_db


def test_disciplines_and_19_communes_loaded(api):
    resp = api.get("/api/v1/disciplines")
    assert resp.status_code == 200
    slugs = {d["slug"] for d in resp.json()}
    assert {"theatre", "danse", "musique", "court-metrage", "clip"} <= slugs
    assert all(
        d["label_i18n"].get("fr") and d["label_i18n"].get("nl") and d["label_i18n"].get("en")
        for d in resp.json()
    )

    resp = api.get("/api/v1/cities?locale=nl")
    assert resp.status_code == 200
    cities = resp.json()
    assert len(cities) == 19
    labels_nl = {c["label"] for c in cities}
    assert {"Brussel", "Elsene", "Vorst", "Ukkel"} <= labels_nl
