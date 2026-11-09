from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

api_v1 = [
    path("", include("kreo.identity.urls")),
    path("", include("kreo.referentials.urls")),
    path("", include("kreo.profiles.urls")),
    path("", include("kreo.media.urls")),
    path("", include("kreo.projects.urls")),
    path("", include("kreo.opportunities.urls")),
    path("", include("kreo.applications.urls")),
    path("", include("kreo.messaging.urls")),
    path("", include("kreo.credits.urls")),
    path("", include("kreo.notifications.urls")),
    path("", include("kreo.moderation.urls")),
    path("health", include("kreo.common.urls")),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(api_v1)),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]

if settings.DEBUG:
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
