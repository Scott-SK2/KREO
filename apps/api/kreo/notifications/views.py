from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.common.exceptions import BusinessRuleError

from . import services
from .catalog import CATALOG
from .models import DeviceToken, Notification, NotificationPreference
from .serializers import (
    DeviceTokenSerializer,
    MarkReadSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)

TAG = ["Notifications"]


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer

    @extend_schema(tags=TAG, summary="Mes notifications (centre in-app)")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.serializer_class.Meta.model.objects.none()
        qs = Notification.objects.filter(recipient=self.request.user)
        if self.request.query_params.get("unread") == "true":
            qs = qs.filter(read_at__isnull=True)
        return qs


class NotificationReadView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Marquer comme lues (toutes ou une liste)",
        request=MarkReadSerializer,
        responses={200: dict},
    )
    def post(self, request):
        ser = MarkReadSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        count = services.mark_read(request.user, ser.validated_data.get("ids"))
        return Response({"updated": count})


class NotificationPreferencesView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Mes préférences par type",
        responses={200: NotificationPreferenceSerializer(many=True)},
    )
    def get(self, request):
        existing = {
            p.event_key: p for p in NotificationPreference.objects.filter(user=request.user)
        }
        rows = []
        for key, spec in CATALOG.items():
            rows.append(
                existing.get(key)
                or NotificationPreference(
                    user=request.user,
                    event_key=key,
                    in_app=spec.in_app,
                    email=spec.email,
                    push=spec.push,
                )
            )
        return Response(NotificationPreferenceSerializer(rows, many=True).data)

    @extend_schema(
        tags=TAG,
        summary="Remplacer mes préférences",
        request=NotificationPreferenceSerializer(many=True),
        responses={200: NotificationPreferenceSerializer(many=True)},
    )
    def put(self, request):
        ser = NotificationPreferenceSerializer(data=request.data, many=True)
        ser.is_valid(raise_exception=True)
        for row in ser.validated_data:
            spec = CATALOG[row["event_key"]]
            NotificationPreference.objects.update_or_create(
                user=request.user,
                event_key=row["event_key"],
                defaults={
                    "in_app": row.get("in_app", spec.in_app),
                    "email": True if spec.mandatory_email else row.get("email", spec.email),
                    "push": row.get("push", spec.push),
                },
            )
        return self.get(request)


class DeviceTokenView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Enregistrer un appareil pour le push (phase L)",
        request=DeviceTokenSerializer,
        responses={201: DeviceTokenSerializer},
    )
    def post(self, request):
        if not settings.FEATURES["push"]:
            raise BusinessRuleError(
                "Les notifications push arrivent au lancement public.",
                problem_type="feature-disabled",
            )
        ser = DeviceTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        token, _ = DeviceToken.objects.update_or_create(
            push_token=ser.validated_data["push_token"],
            defaults={
                "user": request.user,
                "platform": ser.validated_data["platform"],
                "enabled": True,
            },
        )
        return Response(DeviceTokenSerializer(token).data, status=status.HTTP_201_CREATED)

    permission_classes = [permissions.IsAuthenticated]
