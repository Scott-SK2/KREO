from rest_framework import serializers

from kreo.projects.serializers import OwnerSummarySerializer

from .models import CreditEvent, ProjectCredit


class CreditProposeSerializer(serializers.Serializer):
    role_name = serializers.CharField(max_length=160)
    user_id = serializers.UUIDField(required=False, allow_null=True)
    email = serializers.EmailField(required=False, allow_blank=True, default="")

    def validate(self, attrs):
        if not attrs.get("user_id") and not attrs.get("email"):
            raise serializers.ValidationError("Indique un membre (user_id) ou un e-mail.")
        return attrs


class CreditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CreditEvent
        fields = ["id", "to_status", "reason", "created_at"]


class CreditSerializer(serializers.ModelSerializer):
    user = OwnerSummarySerializer(read_only=True)
    project_title = serializers.CharField(source="project.title", read_only=True)
    project_slug = serializers.CharField(source="project.slug", read_only=True)
    allowed_transitions = serializers.SerializerMethodField()
    events = CreditEventSerializer(many=True, read_only=True)

    class Meta:
        model = ProjectCredit
        fields = [
            "id",
            "project_id",
            "project_title",
            "project_slug",
            "user",
            "role_name",
            "status",
            "dispute_reason",
            "confirmed_at",
            "allowed_transitions",
            "events",
            "created_at",
        ]

    def get_allowed_transitions(self, obj) -> list[str]:
        from .services import CREDIT_MACHINE, actor_roles_for

        request = self.context.get("request")
        return CREDIT_MACHINE.targets_from(
            obj.status, actor_roles_for(getattr(request, "user", None), obj)
        )


class PublicCreditSerializer(serializers.ModelSerializer):
    """Seuls les crédits confirmés sont publics."""

    project_title = serializers.CharField(source="project.title", read_only=True)
    project_slug = serializers.CharField(source="project.slug", read_only=True)
    user = OwnerSummarySerializer(read_only=True)

    class Meta:
        model = ProjectCredit
        fields = ["id", "project_title", "project_slug", "user", "role_name", "confirmed_at"]


class CreditTransitionSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20)
    reason = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")
