from django.urls import path

from . import views

urlpatterns = [
    path("projects", views.ProjectListCreateView.as_view(), name="projects"),
    path(
        "projects/invitations/accept",
        views.ProjectInvitationAcceptView.as_view(),
        name="project-invitation-accept",
    ),
    path("projects/<str:project_id>", views.ProjectDetailView.as_view(), name="project-detail"),
    path(
        "projects/<str:project_id>/transition",
        views.ProjectTransitionView.as_view(),
        name="project-transition",
    ),
    path(
        "projects/<str:project_id>/updates",
        views.ProjectUpdatesView.as_view(),
        name="project-updates",
    ),
    path(
        "projects/<str:project_id>/updates/<uuid:update_id>",
        views.ProjectUpdateDeleteView.as_view(),
        name="project-update-delete",
    ),
    path(
        "projects/<str:project_id>/invitations",
        views.ProjectInvitationsView.as_view(),
        name="project-invitations",
    ),
    path(
        "projects/<str:project_id>/members/<uuid:user_id>",
        views.ProjectMemberView.as_view(),
        name="project-member",
    ),
]
