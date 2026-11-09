from django.urls import path

from . import views

urlpatterns = [
    path("profiles/<slug:slug>", views.PublicProfileView.as_view(), name="profile-public"),
    path("me/profile", views.MyProfileView.as_view(), name="me-profile"),
    path("me/profile/media", views.MyProfileMediaView.as_view(), name="me-profile-media"),
]
