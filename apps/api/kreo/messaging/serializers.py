from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from kreo.projects.serializers import OwnerSummarySerializer

from .models import Conversation, Message


class MessageSerializer(serializers.ModelSerializer):
    sender = OwnerSummarySerializer(read_only=True)
    sender_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = Message
        fields = ["id", "sender", "sender_id", "body", "created_at"]


class MessageCreateSerializer(serializers.Serializer):
    body = serializers.CharField(max_length=5000)


class ConversationSerializer(serializers.ModelSerializer):
    application_id = serializers.UUIDField(read_only=True)
    project_title = serializers.CharField(
        source="application.role.opportunity.project.title", read_only=True
    )
    role_title = serializers.CharField(source="application.role.title", read_only=True)
    participants = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    safety_tips = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id",
            "application_id",
            "project_title",
            "role_title",
            "participants",
            "unread_count",
            "last_message",
            "last_message_at",
            "safety_tips",
            "created_at",
        ]

    def get_participants(self, obj) -> list:
        return [
            {"user_id": str(p.user_id), **OwnerSummarySerializer(p.user).data}
            for p in obj.participants.select_related("user__profile")
        ]

    def get_unread_count(self, obj) -> int:
        user = self.context["request"].user
        participant = next((p for p in obj.participants.all() if p.user_id == user.id), None)
        qs = obj.messages.filter(deleted_at__isnull=True).exclude(sender=user)
        if participant and participant.last_read_at:
            qs = qs.filter(created_at__gt=participant.last_read_at)
        return qs.count()

    @extend_schema_field(MessageSerializer(allow_null=True))
    def get_last_message(self, obj):
        last = obj.messages.filter(deleted_at__isnull=True).order_by("-created_at").first()
        return MessageSerializer(last).data if last else None

    def get_safety_tips(self, obj) -> list[str]:
        from .services import SAFETY_TIPS

        return SAFETY_TIPS
