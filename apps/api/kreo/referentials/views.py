from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, viewsets

from kreo.common.permissions import IsAdmin

from .models import City, Discipline
from .serializers import (
    CityAdminSerializer,
    CitySerializer,
    DisciplineAdminSerializer,
    DisciplineSerializer,
)


class LocaleContextMixin:
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        user = getattr(self.request, "user", None)
        ctx["locale"] = (
            self.request.query_params.get("locale")
            or (user.locale if user and user.is_authenticated else None)
            or "fr"
        )
        return ctx


@method_decorator(cache_page(60 * 15), name="get")
class DisciplineListView(LocaleContextMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = DisciplineSerializer
    pagination_class = None
    queryset = Discipline.objects.filter(active=True).select_related("parent")

    @extend_schema(tags=["Référentiels"], summary="Disciplines (taxonomie FR/NL/EN)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@method_decorator(cache_page(60 * 15), name="get")
class CityListView(LocaleContextMixin, generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = CitySerializer
    pagination_class = None
    queryset = City.objects.filter(active=True)

    @extend_schema(tags=["Référentiels"], summary="Communes de référence")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(tags=["Back-office"])
class DisciplineAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = DisciplineAdminSerializer
    queryset = Discipline.objects.all()
    pagination_class = None


@extend_schema(tags=["Back-office"])
class CityAdminViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdmin]
    serializer_class = CityAdminSerializer
    queryset = City.objects.all()
    pagination_class = None
