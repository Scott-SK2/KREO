from rest_framework import serializers

from kreo.media.serializers import MediaAssetSerializer
from kreo.opportunities.serializers import RoleSerializer
from kreo.projects.serializers import OwnerSummarySerializer

from .models import Application, ApplicationEvent, Favorite, SavedSearch


class ApplicationCreateSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=3000, required=False, allow_blank=True, default="")
    availability_confirmed = serializers.BooleanField(required=False, allow_null=True, default=None)
    portfolio_media_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=12
    )
    attachment_ids = serializers.ListField(
        child=serializers.UUIDField(), required=False, default=list, max_length=3
    )


class ApplicationEventSerializer(serializers.ModelSerializer):
    actor = OwnerSummarySerializer(read_only=True)

    class Meta:
        model = ApplicationEvent
        fields = ["id", "from_status", "to_status", "note", "actor", "created_at"]


class ApplicationSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    applicant = OwnerSummarySerializer(read_only=True)
    applicant_id = serializers.UUIDField(read_only=True)
    portfolio_media = MediaAssetSerializer(many=True, read_only=True)
    attachments = MediaAssetSerializer(many=True, read_only=True)
    allowed_transitions = serializers.SerializerMethodField()
    conversation_id = serializers.SerializerMethodField()
    project_title = serializers.CharField(source="role.opportunity.project.title", read_only=True)
    project_slug = serializers.CharField(source="role.opportunity.project.slug", read_only=True)
    opportunity_title = serializers.CharField(source="role.opportunity.title", read_only=True)

    class Meta:
        model = Application
        fields = [
            "id",
            "role",
            "applicant",
            "applicant_id",
            "message",
            "status",
            "availability_confirmed",
            "portfolio_media",
            "attachments",
            "allowed_transitions",
            "conversation_id",
            "project_title",
            "project_slug",
            "opportunity_title",
            "submitted_at",
            "updated_at",
        ]

    def get_allowed_transitions(self, obj) -> list[str]:
        from .services import APPLICATION_MACHINE, actor_roles_for

        request = self.context.get("request")
        return APPLICATION_MACHINE.targets_from(
            obj.status, actor_roles_for(getattr(request, "user", None), obj)
        )

    def get_conversation_id(self, obj) -> str | None:
        conv = getattr(obj, "conversation", None)
        return str(conv.id) if conv else None


class ApplicationListSerializer(ApplicationSerializer):
    class Meta(ApplicationSerializer.Meta):
        fields = [
            f
            for f in ApplicationSerializer.Meta.fields
            if f not in ("portfolio_media", "attachments")
        ]


class ApplicationTransitionSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20)
    note = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class FavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Favorite
        fields = ["id", "target_type", "target_id", "created_at"]
        read_only_fields = ["id", "created_at"]


class SavedSearchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedSearch
        fields = ["id", "name", "filters", "alerts_enabled", "last_notified_at", "created_at"]
        read_only_fields = ["id", "last_notified_at", "created_at"]
