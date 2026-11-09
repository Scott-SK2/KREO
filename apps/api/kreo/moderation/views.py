from django.http import Http404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.pagination import ModerationQueuePagination, OldestFirstCursorPagination
from kreo.common.permissions import IsActiveAccount, IsAdmin, IsModerator
from kreo.common.throttles import ReportsThrottle
from kreo.identity.models import User

from . import serializers, services
from .models import Appeal, AuditLog, Block, ModerationAction, Report

TAG = ["Confiance et modération"]
ADMIN_TAG = ["Back-office"]


class ReportCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsActiveAccount]
    throttle_classes = [ReportsThrottle]

    @extend_schema(
        tags=TAG,
        summary="Signaler un utilisateur, projet, annonce, actualité ou message",
        request=serializers.ReportCreateSerializer,
        responses={201: serializers.ReportSerializer},
    )
    def post(self, request):
        ser = serializers.ReportCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        report = services.create_report(reporter=request.user, **ser.validated_data)
        return Response(serializers.ReportSerializer(report).data, status=status.HTTP_201_CREATED)


class BlockView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=TAG, summary="Mes blocages", responses={200: serializers.BlockSerializer(many=True)}
    )
    def get(self, request):
        return Response(
            serializers.BlockSerializer(Block.objects.filter(blocker=request.user), many=True).data
        )

    @extend_schema(
        tags=TAG,
        summary="Bloquer une personne",
        request=serializers.BlockCreateSerializer,
        responses={201: serializers.BlockSerializer},
    )
    def post(self, request):
        ser = serializers.BlockCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        target = User.objects.alive().filter(id=ser.validated_data["user_id"]).first()
        if target is None:
            raise Http404
        block = services.block_user(request.user, target)
        return Response(serializers.BlockSerializer(block).data, status=status.HTTP_201_CREATED)


class BlockDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(tags=TAG, summary="Débloquer", responses={204: None})
    def delete(self, request, block_id):
        deleted, _ = Block.objects.filter(id=block_id, blocker=request.user).delete()
        if not deleted:
            raise Http404
        return Response(status=status.HTTP_204_NO_CONTENT)


class AppealView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=TAG,
        summary="Faire un recours contre une décision (30 jours, phase L)",
        request=serializers.AppealCreateSerializer,
        responses={201: serializers.AppealSerializer},
    )
    def post(self, request):
        ser = serializers.AppealCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = ModerationAction.objects.filter(id=ser.validated_data["action_id"]).first()
        if action is None:
            raise Http404
        appeal = services.file_appeal(
            appellant=request.user, action=action, body=ser.validated_data["body"]
        )
        return Response(serializers.AppealSerializer(appeal).data, status=status.HTTP_201_CREATED)


class MyModerationDecisionsView(generics.ListAPIView):
    """Décisions me concernant, avec leur motivation."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = serializers.ModerationActionSerializer

    @extend_schema(tags=TAG, summary="Décisions de modération me concernant")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        return ModerationAction.objects.filter(affected_user=self.request.user)


# --- Back-office -----------------------------------------------------------


class AdminReportListView(generics.ListAPIView):
    """File de traitement : priorité (sécurité des personnes d'abord), puis ancienneté."""

    permission_classes = [IsModerator]
    serializer_class = serializers.ReportSerializer
    pagination_class = ModerationQueuePagination

    @extend_schema(tags=ADMIN_TAG, summary="File des signalements")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        qs = Report.objects.all()
        status_filter = self.request.query_params.get("status", "open")
        if status_filter != "all":
            qs = qs.filter(status=status_filter)
        return qs.order_by("priority", "created_at")


class AdminReportActionView(APIView):
    permission_classes = [IsModerator]

    @extend_schema(
        tags=ADMIN_TAG,
        summary="Agir sur un signalement (action journalisée, motivation envoyée)",
        request=serializers.ModerationActionCreateSerializer,
        responses={201: serializers.ModerationActionSerializer},
    )
    def post(self, request, report_id):
        report = Report.objects.filter(id=report_id).first()
        if report is None:
            raise Http404
        ser = serializers.ModerationActionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = services.take_action(
            moderator=request.user,
            report=report,
            target_type=report.target_type,
            target_id=report.target_id,
            **ser.validated_data,
        )
        return Response(
            serializers.ModerationActionSerializer(action).data, status=status.HTTP_201_CREATED
        )


class AdminAppealListView(generics.ListAPIView):
    permission_classes = [IsModerator]
    serializer_class = serializers.AppealSerializer
    pagination_class = OldestFirstCursorPagination

    @extend_schema(tags=ADMIN_TAG, summary="Recours en attente")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        return Appeal.objects.filter(status="open").exclude(action__moderator=self.request.user)


class AdminAppealDecideView(APIView):
    permission_classes = [IsModerator]

    @extend_schema(
        tags=ADMIN_TAG,
        summary="Trancher un recours (autre modérateur)",
        request=serializers.AppealDecisionSerializer,
        responses={200: serializers.AppealSerializer},
    )
    def post(self, request, appeal_id):
        appeal = Appeal.objects.select_related("action").filter(id=appeal_id, status="open").first()
        if appeal is None:
            raise Http404
        ser = serializers.AppealDecisionSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        appeal = services.decide_appeal(moderator=request.user, appeal=appeal, **ser.validated_data)
        return Response(serializers.AppealSerializer(appeal).data)


class AdminAuditView(generics.ListAPIView):
    """Admin : tout le journal. Modérateur : ses propres actions."""

    permission_classes = [IsModerator]
    serializer_class = serializers.AuditLogSerializer

    @extend_schema(tags=ADMIN_TAG, summary="Journal d'audit")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        qs = AuditLog.objects.all()
        if not self.request.user.is_staff:
            qs = qs.filter(actor=self.request.user)
        return qs


class AdminUserStatusView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=ADMIN_TAG,
        summary="Suspendre ou rétablir un compte (hors signalement)",
        request=serializers.ModerationActionCreateSerializer,
        responses={201: serializers.ModerationActionSerializer},
    )
    def post(self, request, user_id):
        target = User.objects.alive().filter(id=user_id).first()
        if target is None:
            raise Http404
        ser = serializers.ModerationActionCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        action = services.take_action(
            moderator=request.user,
            report=None,
            target_type="user",
            target_id=target.id,
            **ser.validated_data,
        )
        return Response(
            serializers.ModerationActionSerializer(action).data, status=status.HTTP_201_CREATED
        )
