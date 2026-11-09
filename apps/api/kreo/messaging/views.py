from django.http import Http404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from kreo.applications.models import Application
from kreo.common.permissions import IsActiveAccount
from kreo.common.throttles import MessagesThrottle
from kreo.moderation.services import audit

from . import serializers, services
from .models import Conversation, Message

TAG = ["Messagerie"]


def _get_conversation(request, conversation_id) -> Conversation:
    conv = (
        Conversation.objects.select_related("application__role__opportunity__project")
        .prefetch_related("participants__user__profile")
        .filter(id=conversation_id)
        .first()
    )
    if conv is None:
        raise Http404
    if services.is_participant(request.user, conv):
        return conv
    if request.user.is_moderator or request.user.is_staff:
        audit(
            request.user,
            "moderation.read_conversation",
            target_type="conversation",
            target_id=conv.id,
            reason=request.headers.get("X-Moderation-Reason", "signalement"),
        )
        return conv
    raise Http404


class ConversationListView(APIView):
    @extend_schema(
        tags=TAG,
        summary="Mes conversations",
        responses={200: serializers.ConversationSerializer(many=True)},
    )
    def get(self, request):
        qs = (
            Conversation.objects.filter(participants__user=request.user)
            .select_related("application__role__opportunity__project")
            .prefetch_related("participants__user__profile")
            .order_by("-last_message_at", "-created_at")
            .distinct()
        )
        return Response(
            serializers.ConversationSerializer(qs, many=True, context={"request": request}).data
        )

    @extend_schema(
        tags=TAG,
        summary="Ouvrir la conversation d'une candidature",
        request={
            "application/json": {
                "type": "object",
                "properties": {"application_id": {"type": "string", "format": "uuid"}},
            }
        },
        responses={201: serializers.ConversationSerializer},
    )
    def post(self, request):
        permissions_ok = IsActiveAccount().has_permission(request, self)
        if not permissions_ok:
            self.permission_denied(request, message=IsActiveAccount.message)
        application = (
            Application.objects.select_related("role__opportunity__project__owner", "applicant")
            .filter(id=request.data.get("application_id"))
            .first()
        )
        if application is None:
            raise Http404
        conv = services.get_or_create_conversation(application=application, actor=request.user)
        conv = _get_conversation(request, conv.id)
        return Response(
            serializers.ConversationSerializer(conv, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationMessagesView(APIView):
    throttle_classes = [MessagesThrottle]

    @extend_schema(
        tags=TAG,
        summary="Messages d'une conversation (polling 15 s : ?after=<iso>)",
        parameters=[OpenApiParameter("after", str)],
        responses={200: serializers.MessageSerializer(many=True)},
    )
    def get(self, request, conversation_id):
        conv = _get_conversation(request, conversation_id)
        qs = Message.objects.filter(conversation=conv, deleted_at__isnull=True).select_related(
            "sender__profile"
        )
        if request.query_params.get("after"):
            qs = qs.filter(created_at__gt=request.query_params["after"])
        return Response(serializers.MessageSerializer(qs[:200], many=True).data)

    @extend_schema(
        tags=TAG,
        summary="Envoyer un message",
        request=serializers.MessageCreateSerializer,
        responses={201: serializers.MessageSerializer},
    )
    def post(self, request, conversation_id):
        if not IsActiveAccount().has_permission(request, self):
            self.permission_denied(request, message=IsActiveAccount.message)
        conv = _get_conversation(request, conversation_id)
        if not services.is_participant(request.user, conv):
            self.permission_denied(request, message="Lecture seule pour la modération.")
        ser = serializers.MessageCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        message = services.send_message(
            conversation=conv, sender=request.user, body=ser.validated_data["body"]
        )
        return Response(serializers.MessageSerializer(message).data, status=status.HTTP_201_CREATED)


class ConversationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=TAG, summary="Marquer la conversation comme lue", request=None, responses={204: None}
    )
    def post(self, request, conversation_id):
        conv = _get_conversation(request, conversation_id)
        services.mark_read(conversation=conv, user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
