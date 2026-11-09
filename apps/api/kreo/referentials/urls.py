from django.urls import include, path
from rest_framework.routers import SimpleRouter

from . import views

router = SimpleRouter(trailing_slash=False)
router.register("admin/disciplines", views.DisciplineAdminViewSet, basename="admin-disciplines")
router.register("admin/cities", views.CityAdminViewSet, basename="admin-cities")

urlpatterns = [
    path("disciplines", views.DisciplineListView.as_view(), name="disciplines"),
    path("cities", views.CityListView.as_view(), name="cities"),
    path("", include(router.urls)),
]
