from django.urls import path

from . import views

urlpatterns = [
    path(
        "roles/<uuid:role_id>/applications",
        views.RoleApplicationsView.as_view(),
        name="role-applications",
    ),
    path("me/applications", views.MyApplicationsView.as_view(), name="me-applications"),
    path("me/inbox", views.ProjectInboxView.as_view(), name="me-inbox"),
    path(
        "applications/<uuid:application_id>",
        views.ApplicationDetailView.as_view(),
        name="application-detail",
    ),
    path(
        "applications/<uuid:application_id>/transition",
        views.ApplicationTransitionView.as_view(),
        name="application-transition",
    ),
    path(
        "applications/<uuid:application_id>/events",
        views.ApplicationEventsView.as_view(),
        name="application-events",
    ),
    path("me/favorites", views.FavoritesView.as_view(), name="me-favorites"),
    path(
        "me/favorites/<int:favorite_id>",
        views.FavoriteDetailView.as_view(),
        name="me-favorite-detail",
    ),
    path("me/saved-searches", views.SavedSearchesView.as_view(), name="me-saved-searches"),
    path(
        "me/saved-searches/<uuid:search_id>",
        views.SavedSearchDetailView.as_view(),
        name="me-saved-search-detail",
    ),
]
