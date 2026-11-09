from django.urls import path

from . import views

urlpatterns = [
    path("opportunities", views.OpportunitySearchView.as_view(), name="opportunities"),
    path(
        "opportunities/<uuid:opportunity_id>",
        views.OpportunityDetailView.as_view(),
        name="opportunity-detail",
    ),
    path(
        "opportunities/<uuid:opportunity_id>/transition",
        views.OpportunityTransitionView.as_view(),
        name="opportunity-transition",
    ),
    path(
        "opportunities/<uuid:opportunity_id>/roles",
        views.RoleCreateView.as_view(),
        name="opportunity-roles",
    ),
    path("roles/<uuid:role_id>", views.RoleDetailView.as_view(), name="role-detail"),
    path(
        "projects/<str:project_id>/opportunities",
        views.ProjectOpportunitiesView.as_view(),
        name="project-opportunities",
    ),
    path(
        "admin/opportunities/pending",
        views.AdminPendingOpportunitiesView.as_view(),
        name="admin-opportunities-pending",
    ),
]
