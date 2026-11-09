from django.urls import path

from . import views

urlpatterns = [
    path("media", views.MediaUploadView.as_view(), name="media-upload"),
    path("media/<uuid:asset_id>", views.MediaDetailView.as_view(), name="media-detail"),
    path("media/file/<path:storage_key>", views.SignedFileView.as_view(), name="media-file"),
]
