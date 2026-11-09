from django.db.models import Q
from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.choices import Visibility
from kreo.common.exceptions import BusinessRuleError
from kreo.common.permissions import IsActiveAccount
from kreo.moderation.services import blocked_user_ids

from . import serializers, services
from .models import PUBLIC_PROJECT_STATUSES, Project, ProjectUpdate
from .permissions import can_view_project, is_project_manager

TAG = ["Projets"]


def _get_project(request, project_id) -> Project:
    project = (
        Project.objects.select_related("owner__profile", "city", "cover")
        .prefetch_related("disciplines", "memberships__user__profile")
        .filter(Q(id=project_id) if _is_uuid(project_id) else Q(slug=project_id))
        .first()
    )
    if project is None or not can_view_project(request.user, project):
        raise Http404
    if request.user.is_authenticated and project.owner_id in blocked_user_ids(request.user):
        if not is_project_manager(request.user, project):
            raise Http404
    return project


def _is_uuid(value) -> bool:
    import uuid

    try:
        uuid.UUID(str(value))
        return True
    except ValueError:
        return False


class ProjectListCreateView(generics.ListAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.ProjectListSerializer

    @extend_schema(
        tags=TAG,
        summary="Projets publics (filtres : discipline, city, status, q, mine)",
        parameters=[
            OpenApiParameter("discipline", str, description="slug de discipline"),
            OpenApiParameter("city", int),
            OpenApiParameter("status", str),
            OpenApiParameter("q", str, description="texte libre (french + unaccent)"),
            OpenApiParameter("mine", bool, description="mes projets (porteur, co-orga, membre)"),
        ],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        params = self.request.query_params
        user = self.request.user
        qs = Project.objects.select_related("owner__profile", "city", "cover").prefetch_related(
            "disciplines"
        )
        if params.get("mine") == "true" and user.is_authenticated:
            qs = qs.filter(Q(owner=user) | Q(memberships__user=user)).distinct()
        else:
            qs = qs.filter(
                status__in=PUBLIC_PROJECT_STATUSES,
                visibility=Visibility.PUBLIC,
                owner__status="active",
            )
            if user.is_authenticated:
                qs = qs.exclude(owner_id__in=blocked_user_ids(user))
        if params.get("discipline"):
            qs = qs.filter(disciplines__slug=params["discipline"])
        if params.get("city"):
            qs = qs.filter(city_id=params["city"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("q"):
            from django.contrib.postgres.search import SearchQuery

            qs = qs.filter(
                search_vector=SearchQuery(
                    params["q"], config="kreo_french", search_type="websearch"
                )
            )
        return qs.distinct()

    @extend_schema(
        tags=TAG,
        summary="Créer un projet (porteur vérifié)",
        request=serializers.ProjectWriteSerializer,
        responses={201: serializers.ProjectSerializer},
    )
    def post(self, request):
        self.permission_classes = [permissions.IsAuthenticated, IsActiveAccount]
        self.check_permissions(request)
        ser = serializers.ProjectWriteSerializer(data=request.data, context={"request": request})
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        project = services.create_project(
            owner=request.user,
            title=data["title"],
            description=data["description"],
            disciplines=data["discipline_ids"],
            city=data.get("city_id"),
            starts_on=data.get("starts_on"),
            ends_on=data.get("ends_on"),
            is_commercial=data["is_commercial"],
            cover=data.get("cover"),
            visibility=data["visibility"],
        )
        return Response(
            serializers.ProjectSerializer(project, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ProjectDetailView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=TAG,
        summary="Page projet (par id ou slug)",
        responses={200: serializers.ProjectSerializer},
    )
    def get(self, request, project_id):
        project = _get_project(request, project_id)
        return Response(serializers.ProjectSerializer(project, context={"request": request}).data)

    @extend_schema(
        tags=TAG,
        summary="Modifier un projet (porteur ou co-orga)",
        request=serializers.ProjectWriteSerializer,
        responses={200: serializers.ProjectSerializer},
    )
    def patch(self, request, project_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        project = _get_project(request, project_id)
        if not is_project_manager(request.user, project):
            raise BusinessRuleError("Seuls le porteur et les co-organisateurs modifient le projet.")
        if project.status == "archived":
            raise BusinessRuleError("Un projet archivé est en lecture seule.")
        ser = serializers.ProjectWriteSerializer(
            data=request.data, partial=True, context={"request": request}
        )
        ser.is_valid(raise_exception=True)
        data = ser.validated_data
        disciplines = data.pop("discipline_ids", None)
        if "city_id" in data:
            project.city = data.pop("city_id")
        for field, value in data.items():
            setattr(project, field, value)
        project.save()
        if disciplines is not None:
            project.disciplines.set(disciplines)
        project = _get_project(request, project.id)
        return Response(serializers.ProjectSerializer(project, context={"request": request}).data)


class ProjectTransitionView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Changer le statut du projet (409 si transition interdite)",
        request=serializers.TransitionSerializer,
        responses={200: serializers.ProjectSerializer},
    )
    def post(self, request, project_id):
        project = _get_project(request, project_id)
        ser = serializers.TransitionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        project = services.transition_project(
            project=project, target=ser.validated_data["status"], actor=request.user
        )
        project = _get_project(request, project.id)
        return Response(serializers.ProjectSerializer(project, context={"request": request}).data)


class ProjectUpdatesView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        tags=TAG,
        summary="Actualités du projet",
        responses={200: serializers.ProjectUpdateSerializer(many=True)},
    )
    def get(self, request, project_id):
        project = _get_project(request, project_id)
        qs = (
            ProjectUpdate.objects.filter(project=project, deleted_at__isnull=True)
            .select_related("author__profile")
            .prefetch_related("media")
        )
        return Response(serializers.ProjectUpdateSerializer(qs, many=True).data)

    @extend_schema(
        tags=TAG,
        summary="Publier une actualité (texte + 4 photos max)",
        request=serializers.ProjectUpdateSerializer,
        responses={201: serializers.ProjectUpdateSerializer},
    )
    def post(self, request, project_id):
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        IsActiveAccount().has_permission(request, self) or self.permission_denied(request)
        project = _get_project(request, project_id)
        ser = serializers.ProjectUpdateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        update = services.post_update(
            project=project,
            actor=request.user,
            body=ser.validated_data["body"],
            media_ids=ser.validated_data.get("media_ids", []),
        )
        return Response(
            serializers.ProjectUpdateSerializer(update).data, status=status.HTTP_201_CREATED
        )


class ProjectUpdateDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=TAG, summary="Retirer une actualité", responses={204: None})
    def delete(self, request, project_id, update_id):
        project = _get_project(request, project_id)
        update = ProjectUpdate.objects.filter(
            id=update_id, project=project, deleted_at__isnull=True
        ).first()
        if update is None:
            raise Http404
        if not (
            is_project_manager(request.user, project)
            or request.user.is_moderator
            or request.user.is_staff
        ):
            raise BusinessRuleError("Action réservée au porteur et aux co-organisateurs.")
        from django.utils import timezone

        update.deleted_at = timezone.now()
        update.save(update_fields=["deleted_at"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProjectInvitationsView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Inviter un co-organisateur ou un membre (lien ou e-mail, 7 jours)",
        request=serializers.InvitationCreateSerializer,
        responses={201: serializers.InvitationSerializer},
    )
    def post(self, request, project_id):
        project = _get_project(request, project_id)
        ser = serializers.InvitationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        invitation, raw = services.invite(project=project, actor=request.user, **ser.validated_data)
        data = serializers.InvitationSerializer(invitation).data
        data["link_token"] = raw
        return Response(data, status=status.HTTP_201_CREATED)

    @extend_schema(
        tags=TAG,
        summary="Invitations en cours",
        responses={200: serializers.InvitationSerializer(many=True)},
    )
    def get(self, request, project_id):
        project = _get_project(request, project_id)
        if not is_project_manager(request.user, project):
            raise BusinessRuleError("Action réservée au porteur et aux co-organisateurs.")
        qs = project.invitations.filter(accepted_at__isnull=True).order_by("-created_at")
        return Response(serializers.InvitationSerializer(qs, many=True).data)


class ProjectInvitationAcceptView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]

    @extend_schema(
        tags=TAG,
        summary="Accepter une invitation",
        request=serializers.InvitationAcceptSerializer,
        responses={200: serializers.ProjectMemberSerializer},
    )
    def post(self, request):
        ser = serializers.InvitationAcceptSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        member = services.accept_invitation(
            raw_token=ser.validated_data["token"], user=request.user
        )
        return Response(serializers.ProjectMemberSerializer(member).data)


class ProjectMemberView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=TAG, summary="Retirer un membre ou co-organisateur (ou quitter)", responses={204: None}
    )
    def delete(self, request, project_id, user_id):
        project = _get_project(request, project_id)
        services.remove_member(project=project, actor=request.user, user_id=user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
