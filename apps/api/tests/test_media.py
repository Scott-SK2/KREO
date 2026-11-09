import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

pytestmark = pytest.mark.django_db


def _png(size=(64, 64)):
    buf = io.BytesIO()
    Image.new("RGB", size, "#8B7262").save(buf, format="PNG")
    return buf.getvalue()


def test_upload_validates_mime_size_and_generates_variants(api, candidate, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    api.force_authenticate(candidate)
    resp = api.post(
        "/api/v1/media",
        {"file": SimpleUploadedFile("a.png", _png(), "image/png"), "alt_text": "Portrait"},
        format="multipart",
    )
    assert resp.status_code == 201, resp.content
    body = resp.json()
    assert set(body["variants"]) == {"sm", "md", "lg"} and body["mime_type"] == "image/png"
    assert "sig=" in body["url"] and "expires=" in body["url"]
    # URL signée servie ; signature falsifiée refusée
    path = body["url"].split("http://localhost:8000")[1]
    assert api.get(path).status_code == 200
    assert api.get(path.replace("sig=", "sig=x")).status_code == 404

    # Faux type MIME (texte renommé en .png)
    resp = api.post(
        "/api/v1/media",
        {"file": SimpleUploadedFile("b.png", b"pas une image", "image/png")},
        format="multipart",
    )
    assert resp.status_code == 415
    # Trop gros
    settings.MEDIA_MAX_BYTES = 10
    resp = api.post(
        "/api/v1/media",
        {"file": SimpleUploadedFile("c.png", _png(), "image/png")},
        format="multipart",
    )
    assert resp.status_code == 413
