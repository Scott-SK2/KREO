from rest_framework import serializers

from .catalog import CATALOG
from .models import DeviceToken, Notification, NotificationPreference


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ["id", "event_key", "title", "payload", "deep_link", "read_at", "created_at"]

    def get_title(self, obj) -> str:
        return obj.payload.get("title") or CATALOG[obj.event_key].title_fr


class MarkReadSerializer(serializers.Serializer):
    ids = serializers.ListField(child=serializers.UUIDField(), required=False)


class NotificationPreferenceSerializer(serializers.ModelSerializer):
    mandatory_email = serializers.SerializerMethodField()

    class Meta:
        model = NotificationPreference
        fields = ["event_key", "in_app", "email", "push", "mandatory_email"]

    def get_mandatory_email(self, obj) -> bool:
        return CATALOG[obj.event_key].mandatory_email

    def validate_event_key(self, value):
        if value not in CATALOG:
            raise serializers.ValidationError("Type de notification inconnu.")
        return value


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ["id", "platform", "push_token", "enabled", "updated_at"]
        read_only_fields = ["id", "updated_at"]
