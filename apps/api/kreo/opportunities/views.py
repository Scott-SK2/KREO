from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.exceptions import BusinessRuleError
from kreo.common.pagination import PublishedAtCursorPagination
from kreo.common.permissions import IsActiveAccount
from kreo.common.throttles import OpportunitiesDailyThrottle
from kreo.projects.permissions import can_view_project, is_project_manager
from kreo.projects.views import _get_project

from . import serializers, services
from .filters import search_opportunities
from .models import Opportunity, OpportunityRole

TAG = ["Annonces"]


def _get_opportunity(request, opportunity_id) -> Opportunity:
    opp = (
        Opportunity.objects.select_related(
            "project__owner__profile", "project__city", "created_by__profile"
        )
        .prefetch_related("roles__discipline", "roles__city", "project__disciplines")
        .filter(id=opportunity_id)
        .first()
    )
    if opp is None:
        raise Http404
    manager = request.user.is_authenticated and is_project_manager(request.user, opp.project)
    if opp.status == "draft" and not manager and not getattr(request.user, "is_moderator", False):
        raise Http404
    if not can_view_project(request.user, opp.project) and not manager:
        raise Http404
    return opp


class OpportunitySearchView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.OpportunityListSerializer
    pagination_class = PublishedAtCursorPagination

    @extend_schema(
        tags=TAG,
        summary="Rechercher des annonces ouvertes",
        parameters=[
            OpenApiParameter("q", str, description="Texte libre : « theatre » trouve « théâtre »"),
            OpenApiParameter("discipline", str, description="slugs séparés par des virgules"),
            OpenApiParameter("city", str, description="ids de communes séparés par des virgules"),
            OpenApiParameter("compensation", str, description="paid,volunteer,expenses,negotiable"),
            OpenApiParameter("beginner_friendly", bool),
            OpenApiParameter("deadline_before", str),
            OpenApiParameter("deadline_after", str),
            OpenApiParameter("starts_after", str),
            OpenApiParameter("level", str),
            OpenApiParameter("sort", str, description="recent (défaut) ou relevance"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return search_opportunities(self.request.query_params, self.request.user)


class ProjectOpportunitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]
    throttle_classes = [OpportunitiesDailyThrottle]

    @extend_schema(
        tags=TAG,
        summary="Annonces d'un projet (brouillons inclus pour l'équipe)",
        responses={200: serializers.OpportunitySerializer(many=True)},
    )
    def get(self, request, project_id):
        project = _get_project(request, project_id)
        qs = project.opportunities.prefetch_related("roles")
        if not is_project_manager(request.user, project):
            qs = qs.exclude(status="draft")
        return Response(
            serializers.OpportunitySerializer(qs, many=True, context={"request": request}).data
        )

    @extend_schema(
        tags=TAG,
        summary="Créer une annonce multi-rôles (5 par jour en bêta)",
        request=serializers.OpportunityWriteSerializer,
        responses={201: serializers.OpportunitySerializer},
    )
    def post(self, request, project_id):
        project = _get_project(request, project_id)
        ser = serializers.OpportunityWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        opp = services.create_opportunity(
            project=project,
            actor=request.user,
            title=data["title"],
            description=data["description"],
            has_intimate_scene=data["has_intimate_scene"],
            template_discipline=data.get("template_discipline"),
            roles=data.get("roles") or [],
        )
        opp = _get_opportunity(request, opp.id)
        return Response(
            serializers.OpportunitySerializer(opp, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class OpportunityDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=TAG, summary="Page annonce", responses={200: serializers.OpportunitySerializer}
    )
    def get(self, request, opportunity_id):
        opp = _get_opportunity(request, opportunity_id)
        return Response(serializers.OpportunitySerializer(opp, context={"request": request}).data)

    @extend_schema(
        tags=TAG,
        summary="Modifier une annonce (titre, description, scène intime)",
        request=serializers.OpportunityWriteSerializer,
        responses={200: serializers.OpportunitySerializer},
    )
    def patch(self, request, opportunity_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        opp = _get_opportunity(request, opportunity_id)
        if not is_project_manager(request.user, opp.project):
            raise BusinessRuleError("Seuls le porteur et les co-organisateurs modifient l'annonce.")
        if opp.status in ("closed", "cancelled"):
            raise BusinessRuleError("Cette annonce est fermée.")
        ser = serializers.OpportunityWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        roles = data.pop("roles", None)
        for field, value in data.items():
            setattr(opp, field, value)
        if "has_intimate_scene" in data and data["has_intimate_scene"]:
            opp.moderated_at = None  # nouvelle vérification requise
        opp.save()
        if roles:
            for role in roles:
                services.add_role(opportunity=opp, actor=request.user, **role)
        opp = _get_opportunity(request, opp.id)
        return Response(serializers.OpportunitySerializer(opp, context={"request": request}).data)


class OpportunityTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Publier, fermer ou annuler une annonce (409 si interdit)",
        request=serializers.OpportunityTransitionSerializer,
        responses={200: serializers.OpportunitySerializer},
    )
    def post(self, request, opportunity_id):
        opp = _get_opportunity(request, opportunity_id)
        ser = serializers.OpportunityTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        opp = services.transition_opportunity(
            opportunity=opp, target=ser.validated_data["status"], actor=request.user
        )
        opp = _get_opportunity(request, opp.id)
        return Response(serializers.OpportunitySerializer(opp, context={"request": request}).data)


class RoleDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Modifier un rôle",
        request=serializers.RoleWriteSerializer,
        responses={200: serializers.RoleSerializer},
    )
    def patch(self, request, role_id):
        role = (
            OpportunityRole.objects.select_related("opportunity__project")
            .filter(id=role_id)
            .first()
        )
        if role is None:
            raise Http404
        if not is_project_manager(request.user, role.opportunity.project):
            raise BusinessRuleError("Seuls le porteur et les co-organisateurs modifient un rôle.")
        if role.status == "closed":
            raise BusinessRuleError("Ce rôle est fermé.")
        ser = serializers.RoleWriteSerializer(data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        services.validate_role_rules(
            project=role.opportunity.project,
            compensation=data.get("compensation", role.compensation),
            requirements=data.get("requirements", role.requirements),
        )
        if "slots" in data and data["slots"] < role.accepted_count:
            raise BusinessRuleError(
                "Le nombre de places ne peut pas être inférieur aux acceptations."
            )
        for field, value in data.items():
            setattr(role, field, value)
        role.save()
        return Response(serializers.RoleSerializer(role, context={"request": request}).data)

    @extend_schema(
        tags=TAG,
        summary="Fermer un rôle (refus courtois automatique des candidatures ouvertes)",
        request=serializers.RoleStatusSerializer,
        responses={200: serializers.RoleSerializer},
    )
    def post(self, request, role_id):
        role = (
            OpportunityRole.objects.select_related("opportunity__project")
            .filter(id=role_id)
            .first()
        )
        if role is None:
            raise Http404
        ser = serializers.RoleStatusSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        role = services.close_role(role=role, actor=request.user)
        return Response(serializers.RoleSerializer(role, context={"request": request}).data)

    @extend_schema(tags=TAG, summary="Supprimer un rôle sans candidature", responses={204: None})
    def delete(self, request, role_id):
        role = (
            OpportunityRole.objects.select_related("opportunity__project")
            .filter(id=role_id)
            .first()
        )
        if role is None:
            raise Http404
        if not is_project_manager(request.user, role.opportunity.project):
            raise BusinessRuleError("Action réservée au porteur et aux co-organisateurs.")
        if role.applications.exists():
            raise BusinessRuleError(
                "Ce rôle a des candidatures : ferme-le plutôt que de le supprimer."
            )
        if role.opportunity.roles.count() == 1 and role.opportunity.status == "open":
            raise BusinessRuleError("Une annonce publiée garde au moins un rôle.")
        role.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Ajouter un rôle à une annonce",
        request=serializers.RoleWriteSerializer,
        responses={201: serializers.RoleSerializer},
    )
    def post(self, request, opportunity_id):
        opp = _get_opportunity(request, opportunity_id)
        ser = serializers.RoleWriteSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        role = services.add_role(opportunity=opp, actor=request.user, **ser.validated_data)
        return Response(
            serializers.RoleSerializer(role, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class AdminPendingOpportunitiesView(generics.ListAPIView):
    """Annonces avec scène intime en attente de vérification."""

    from kreo.common.permissions import IsModerator

    permission_classes = [IsModerator]
    serializer_class = serializers.OpportunitySerializer
    pagination_class = None

    @extend_schema(
        tags=["Back-office"], summary="Annonces en attente de vérification (scène intime)"
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return Opportunity.objects.filter(
            has_intimate_scene=True, moderated_at__isnull=True, status="draft"
        ).select_related("project")
