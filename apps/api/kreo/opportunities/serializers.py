from rest_framework import serializers

from kreo.common.choices import CompensationType, RoleStatus
from kreo.projects.serializers import OwnerSummarySerializer, ProjectListSerializer
from kreo.referentials.models import City, Discipline
from kreo.referentials.serializers import CitySerializer, DisciplineSerializer

from .models import Opportunity, OpportunityRole


class RoleWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=150)
    description = serializers.CharField(
        max_length=5000, required=False, allow_blank=True, default=""
    )
    discipline = serializers.PrimaryKeyRelatedField(
        queryset=Discipline.objects.filter(active=True), required=False, allow_null=True
    )
    requirements = serializers.DictField(required=False, default=dict)
    slots = serializers.IntegerField(min_value=1, max_value=200, default=1)
    compensation = serializers.ChoiceField(choices=CompensationType.choices)
    compensation_details = serializers.CharField(
        max_length=1000, required=False, allow_blank=True, default=""
    )
    city = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(active=True), required=False, allow_null=True
    )
    deadline_at = serializers.DateTimeField(required=False, allow_null=True)
    beginner_friendly = serializers.BooleanField(default=False)


class RoleSerializer(serializers.ModelSerializer):
    discipline = DisciplineSerializer(read_only=True)
    city = CitySerializer(read_only=True)
    accepted_count = serializers.IntegerField(read_only=True)
    opportunity_id = serializers.UUIDField(read_only=True)
    my_application_id = serializers.SerializerMethodField()

    class Meta:
        model = OpportunityRole
        fields = [
            "id",
            "opportunity_id",
            "title",
            "description",
            "discipline",
            "requirements",
            "slots",
            "accepted_count",
            "status",
            "compensation",
            "compensation_details",
            "city",
            "deadline_at",
            "beginner_friendly",
            "my_application_id",
            "created_at",
        ]

    def get_my_application_id(self, obj) -> str | None:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None
        app = obj.applications.filter(applicant=request.user).only("id").first()
        return str(app.id) if app else None


class OpportunityWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    description = serializers.CharField(max_length=20000)
    has_intimate_scene = serializers.BooleanField(default=False)
    template_discipline = serializers.PrimaryKeyRelatedField(
        queryset=Discipline.objects.filter(active=True), required=False, allow_null=True
    )
    roles = RoleWriteSerializer(many=True, required=False)


class OpportunitySerializer(serializers.ModelSerializer):
    project = ProjectListSerializer(read_only=True)
    created_by = OwnerSummarySerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)
    allowed_transitions = serializers.SerializerMethodField()
    owner_response_time_hours = serializers.SerializerMethodField()
    safety_tips = serializers.SerializerMethodField()

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "title",
            "description",
            "status",
            "has_intimate_scene",
            "moderated_at",
            "project",
            "created_by",
            "roles",
            "allowed_transitions",
            "owner_response_time_hours",
            "safety_tips",
            "published_at",
            "closed_at",
            "created_at",
            "updated_at",
        ]

    def get_allowed_transitions(self, obj) -> list[str]:
        from kreo.projects.permissions import project_roles

        from .services import OPPORTUNITY_MACHINE

        request = self.context.get("request")
        return OPPORTUNITY_MACHINE.targets_from(
            obj.status, project_roles(getattr(request, "user", None), obj.project)
        )

    def get_owner_response_time_hours(self, obj) -> float | None:
        """Délai médian de première réponse du porteur : un fait mesuré, pas une note."""
        from kreo.applications.models import OwnerResponseStat

        stat = OwnerResponseStat.objects.filter(user_id=obj.project.owner_id).first()
        return stat.median_hours if stat else None

    def get_safety_tips(self, obj) -> list[str]:
        return [
            "Rencontre dans un lieu public ou professionnel.",
            "Ne paie jamais pour candidater ou participer.",
            "Signale toute demande déplacée.",
        ]


class OpportunityListSerializer(serializers.ModelSerializer):
    project = ProjectListSerializer(read_only=True)
    roles = RoleSerializer(many=True, read_only=True)

    class Meta:
        model = Opportunity
        fields = [
            "id",
            "title",
            "status",
            "has_intimate_scene",
            "project",
            "roles",
            "published_at",
            "created_at",
        ]


class OpportunityTransitionSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20)


class RoleStatusSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=[(RoleStatus.CLOSED, "closed")])
