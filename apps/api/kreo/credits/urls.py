from django.urls import path

from . import views

urlpatterns = [
    path(
        "projects/<str:project_id>/credits",
        views.ProjectCreditsView.as_view(),
        name="project-credits",
    ),
    path(
        "credits/<uuid:credit_id>/transition",
        views.CreditTransitionView.as_view(),
        name="credit-transition",
    ),
    path("me/credits", views.MyCreditsView.as_view(), name="me-credits"),
    path(
        "profiles/<slug:slug>/credits", views.ProfileCreditsView.as_view(), name="profile-credits"
    ),
]
