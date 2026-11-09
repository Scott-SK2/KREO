from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.permissions import IsActiveAccount
from kreo.identity.models import User
from kreo.profiles.models import ArtistProfile
from kreo.projects.permissions import is_project_manager
from kreo.projects.views import _get_project

from . import serializers, services
from .models import ProjectCredit

TAG = ["Crédits"]


class ProjectCreditsView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=TAG,
        summary="Crédits d'un projet (confirmés pour tous ; tous pour l'équipe)",
        responses={200: serializers.CreditSerializer(many=True)},
    )
    def get(self, request, project_id):
        project = _get_project(request, project_id)
        qs = project.credits.select_related("user__profile", "project").prefetch_related("events")
        if not (request.user.is_authenticated and is_project_manager(request.user, project)):
            qs = qs.filter(status="confirmed")
            return Response(serializers.PublicCreditSerializer(qs, many=True).data)
        return Response(
            serializers.CreditSerializer(qs, many=True, context={"request": request}).data
        )

    @extend_schema(
        tags=TAG,
        summary="Proposer un crédit (projet terminé ; membre ou e-mail non inscrit)",
        request=serializers.CreditProposeSerializer,
        responses={201: serializers.CreditSerializer},
    )
    def post(self, request, project_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        if not IsActiveAccount().has_permission(request, self):
            self.permission_denied(request, message=IsActiveAccount.message)
        project = _get_project(request, project_id)
        ser = serializers.CreditProposeSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = None
        if ser.validated_data.get("user_id"):
            user = User.objects.alive().filter(id=ser.validated_data["user_id"]).first()
            if user is None:
                raise Http404
        credit = services.propose_credit(
            project=project,
            actor=request.user,
            role_name=ser.validated_data["role_name"],
            user=user,
            email=ser.validated_data.get("email", ""),
        )
        return Response(
            serializers.CreditSerializer(credit, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class CreditTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Confirmer, refuser ou contester un crédit (409 si interdit)",
        request=serializers.CreditTransitionSerializer,
        responses={200: serializers.CreditSerializer},
    )
    def post(self, request, credit_id):
        credit = ProjectCredit.objects.select_related("project").filter(id=credit_id).first()
        if credit is None:
            raise Http404
        ser = serializers.CreditTransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        credit = services.transition_credit(
            credit=credit,
            target=ser.validated_data["status"],
            actor=request.user,
            reason=ser.validated_data["reason"],
        )
        return Response(serializers.CreditSerializer(credit, context={"request": request}).data)


class MyCreditsView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Mes crédits (tous statuts)",
        responses={200: serializers.CreditSerializer(many=True)},
    )
    def get(self, request):
        qs = (
            ProjectCredit.objects.filter(user=request.user)
            .select_related("project", "user__profile")
            .prefetch_related("events")
            .order_by("-created_at")
        )
        return Response(
            serializers.CreditSerializer(qs, many=True, context={"request": request}).data
        )


class ProfileCreditsView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=TAG,
        summary="Crédits confirmés d'un profil",
        responses={200: serializers.PublicCreditSerializer(many=True)},
    )
    def get(self, request, slug):
        profile = ArtistProfile.objects.filter(slug=slug).first()
        if profile is None:
            raise Http404
        qs = (
            ProjectCredit.objects.filter(user=profile.user, status="confirmed")
            .select_related("project", "user__profile")
            .order_by("-confirmed_at")
        )
        return Response(serializers.PublicCreditSerializer(qs, many=True).data)
