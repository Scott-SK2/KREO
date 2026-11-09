from django.conf import settings
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.exceptions import BusinessRuleError
from kreo.common.pagination import SubmittedAtCursorPagination
from kreo.common.permissions import IsActiveAccount
from kreo.common.throttles import ApplicationsDailyThrottle
from kreo.moderation.services import audit
from kreo.opportunities.models import OpportunityRole
from kreo.projects.permissions import is_project_manager

from . import serializers, services
from .models import Application, Favorite, SavedSearch

TAG = ["Candidatures"]


def _get_application(request, application_id) -> Application:
    app = (
        Application.objects.select_related(
            "role__opportunity__project__owner",
            "applicant__profile",
            "role__discipline",
            "role__city",
        )
        .prefetch_related("portfolio_media", "attachments")
        .filter(id=application_id)
        .first()
    )
    if app is None:
        raise Http404
    if services.can_view_application(request.user, app):
        return app
    if request.user.is_moderator or request.user.is_staff:
        # Lecture par un modérateur : journalisée avec motif (signalement).
        audit(
            request.user,
            "moderation.read_application",
            target_type="application",
            target_id=app.id,
            reason=request.headers.get("X-Moderation-Reason", "signalement"),
        )
        return app
    raise Http404


class RoleApplicationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]
    throttle_classes = [ApplicationsDailyThrottle]

    @extend_schema(
        tags=TAG,
        summary="Candidater à un rôle (20 par jour en bêta)",
        request=serializers.ApplicationCreateSerializer,
        responses={201: serializers.ApplicationSerializer},
    )
    def post(self, request, role_id):
        role = (
            OpportunityRole.objects.select_related("opportunity__project")
            .filter(id=role_id)
            .first()
        )
        if role is None or role.opportunity.status == "draft":
            raise Http404
        ser = serializers.ApplicationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        app = services.apply(role=role, applicant=request.user, **ser.validated_data)
        app = _get_application(request, app.id)
        return Response(
            serializers.ApplicationSerializer(app, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )

    @extend_schema(
        tags=TAG,
        summary="Boîte des candidats d'un rôle (porteur, co-orga)",
        parameters=[OpenApiParameter("status", str)],
        responses={200: serializers.ApplicationListSerializer(many=True)},
    )
    def get(self, request, role_id):
        role = (
            OpportunityRole.objects.select_related("opportunity__project")
            .filter(id=role_id)
            .first()
        )
        if role is None:
            raise Http404
        if not is_project_manager(request.user, role.opportunity.project):
            raise BusinessRuleError(
                "Seuls le porteur et les co-organisateurs voient les candidatures."
            )
        qs = role.applications.select_related(
            "applicant__profile", "role__opportunity__project"
        ).order_by("-submitted_at")
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        return Response(
            serializers.ApplicationListSerializer(qs, many=True, context={"request": request}).data
        )


class MyApplicationsView(generics.ListAPIView):
    serializer_class = serializers.ApplicationListSerializer
    pagination_class = SubmittedAtCursorPagination

    @extend_schema(
        tags=TAG, summary="Mes candidatures", parameters=[OpenApiParameter("status", str)]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        qs = Application.objects.filter(applicant=self.request.user).select_related(
            "role__opportunity__project", "role__discipline", "role__city", "applicant__profile"
        )
        if self.request.query_params.get("status"):
            qs = qs.filter(status=self.request.query_params["status"])
        return qs


class ProjectInboxView(APIView):
    """Boîte des candidats du porteur : toutes les candidatures de ses projets."""

    @extend_schema(
        tags=TAG,
        summary="Boîte des candidats (tous mes projets)",
        parameters=[OpenApiParameter("status", str), OpenApiParameter("project", str)],
        responses={200: serializers.ApplicationListSerializer(many=True)},
    )
    def get(self, request):
        from django.db.models import Q

        qs = (
            Application.objects.filter(
                Q(role__opportunity__project__owner=request.user)
                | Q(
                    role__opportunity__project__memberships__user=request.user,
                    role__opportunity__project__memberships__role="manager",
                )
            )
            .select_related("applicant__profile", "role__opportunity__project")
            .distinct()
            .order_by("-submitted_at")
        )
        if request.query_params.get("status"):
            qs = qs.filter(status=request.query_params["status"])
        if request.query_params.get("project"):
            qs = qs.filter(role__opportunity__project_id=request.query_params["project"])
        return Response(
            serializers.ApplicationListSerializer(
                qs[:200], many=True, context={"request": request}
            ).data
        )


class ApplicationDetailView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Détail d'une candidature (passe en « vue » pour un responsable)",
        responses={200: serializers.ApplicationSerializer},
    )
    def get(self, request, application_id):
        app = _get_application(request, application_id)
        app = services.mark_viewed(app, request.user)
        app.refresh_from_db()
        return Response(serializers.ApplicationSerializer(app, context={"request": request}).data)


class ApplicationTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Changer l'étape d'une candidature (409 si interdit)",
        request=serializers.ApplicationTransitionSerializer,
        responses={200: serializers.ApplicationSerializer},
    )
    def post(self, request, application_id):
        app = _get_application(request, application_id)
        ser = serializers.ApplicationTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        app = services.transition_application(
            application=app,
            target=ser.validated_data["status"],
            actor=request.user,
            note=ser.validated_data["note"],
        )
        app = _get_application(request, app.id)
        return Response(serializers.ApplicationSerializer(app, context={"request": request}).data)


class ApplicationEventsView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Historique immuable d'une candidature",
        responses={200: serializers.ApplicationEventSerializer(many=True)},
    )
    def get(self, request, application_id):
        app = _get_application(request, application_id)
        return Response(
            serializers.ApplicationEventSerializer(
                app.events.select_related("actor__profile"), many=True
            ).data
        )


class FavoritesView(APIView):
    def _check(self):
        if not settings.FEATURES["saved_searches"]:
            raise BusinessRuleError(
                "Les favoris arrivent au lancement public.", problem_type="feature-disabled"
            )

    @extend_schema(
        tags=["Recherches et favoris"],
        summary="Mes favoris (phase L)",
        responses={200: serializers.FavoriteSerializer(many=True)},
    )
    def get(self, request):
        self._check()
        return Response(
            serializers.FavoriteSerializer(
                Favorite.objects.filter(user=request.user), many=True
            ).data
        )

    @extend_schema(
        tags=["Recherches et favoris"],
        summary="Ajouter un favori",
        request=serializers.FavoriteSerializer,
        responses={201: serializers.FavoriteSerializer},
    )
    def post(self, request):
        self._check()
        ser = serializers.FavoriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        fav, _ = Favorite.objects.get_or_create(user=request.user, **ser.validated_data)
        return Response(serializers.FavoriteSerializer(fav).data, status=status.HTTP_201_CREATED)


class FavoriteDetailView(APIView):
    @extend_schema(
        tags=["Recherches et favoris"], summary="Retirer un favori", responses={204: None}
    )
    def delete(self, request, favorite_id):
        Favorite.objects.filter(id=favorite_id, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SavedSearchesView(APIView):
    def _check(self):
        if not settings.FEATURES["saved_searches"]:
            raise BusinessRuleError(
                "Les recherches sauvegardées arrivent au lancement public.",
                problem_type="feature-disabled",
            )

    @extend_schema(
        tags=["Recherches et favoris"],
        summary="Mes recherches sauvegardées (phase L)",
        responses={200: serializers.SavedSearchSerializer(many=True)},
    )
    def get(self, request):
        self._check()
        return Response(
            serializers.SavedSearchSerializer(
                SavedSearch.objects.filter(user=request.user), many=True
            ).data
        )

    @extend_schema(
        tags=["Recherches et favoris"],
        summary="Sauvegarder une recherche (alerte opt-in)",
        request=serializers.SavedSearchSerializer,
        responses={201: serializers.SavedSearchSerializer},
    )
    def post(self, request):
        self._check()
        ser = serializers.SavedSearchSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        saved = SavedSearch.objects.create(user=request.user, **ser.validated_data)
        return Response(
            serializers.SavedSearchSerializer(saved).data, status=status.HTTP_201_CREATED
        )


class SavedSearchDetailView(APIView):
    @extend_schema(
        tags=["Recherches et favoris"],
        summary="Supprimer une recherche sauvegardée",
        responses={204: None},
    )
    def delete(self, request, search_id):
        SavedSearch.objects.filter(id=search_id, user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
