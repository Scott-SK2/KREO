from rest_framework import serializers

from kreo.common.choices import ProjectMemberRole, Visibility
from kreo.media.models import MediaAsset
from kreo.media.serializers import MediaAssetSerializer
from kreo.referentials.models import City, Discipline
from kreo.referentials.serializers import CitySerializer, DisciplineSerializer

from .models import Project, ProjectInvitation, ProjectMember, ProjectUpdate


class OwnerSummarySerializer(serializers.Serializer):
    """Résumé public d'un membre : slug et nom d'affichage uniquement."""

    slug = serializers.CharField(source="profile.slug", default=None)
    display_name = serializers.CharField(source="profile.display_name", default="Membre KREO")
    is_verified = serializers.SerializerMethodField()

    def get_is_verified(self, user) -> bool:
        return user.phone_verified_at is not None


class ProjectMemberSerializer(serializers.ModelSerializer):
    user = OwnerSummarySerializer(read_only=True)
    user_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = ProjectMember
        fields = ["user_id", "user", "role", "role_title", "joined_at"]


class ProjectSerializer(serializers.ModelSerializer):
    owner = OwnerSummarySerializer(read_only=True)
    disciplines = DisciplineSerializer(many=True, read_only=True)
    city = CitySerializer(read_only=True)
    cover = MediaAssetSerializer(read_only=True)
    members = ProjectMemberSerializer(source="memberships", many=True, read_only=True)
    my_roles = serializers.SerializerMethodField()
    allowed_transitions = serializers.SerializerMethodField()
    open_roles_count = serializers.SerializerMethodField()

    class Meta:
        model = Project
        fields = [
            "id",
            "slug",
            "title",
            "description",
            "status",
            "is_commercial",
            "visibility",
            "starts_on",
            "ends_on",
            "city",
            "cover",
            "disciplines",
            "owner",
            "members",
            "my_roles",
            "allowed_transitions",
            "open_roles_count",
            "published_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]

    def _roles(self, obj):
        from .permissions import project_roles

        request = self.context.get("request")
        return project_roles(getattr(request, "user", None), obj)

    def get_my_roles(self, obj) -> list[str]:
        return sorted(self._roles(obj))

    def get_allowed_transitions(self, obj) -> list[str]:
        from .services import PROJECT_MACHINE

        return PROJECT_MACHINE.targets_from(obj.status, self._roles(obj))

    def get_open_roles_count(self, obj) -> int:
        from kreo.opportunities.models import OpportunityRole

        return OpportunityRole.objects.filter(
            opportunity__project=obj, opportunity__status="open", status="open"
        ).count()


class ProjectListSerializer(serializers.ModelSerializer):
    owner = OwnerSummarySerializer(read_only=True)
    disciplines = DisciplineSerializer(many=True, read_only=True)
    city = CitySerializer(read_only=True)
    cover = MediaAssetSerializer(read_only=True)

    class Meta:
        model = Project
        fields = [
            "id",
            "slug",
            "title",
            "status",
            "is_commercial",
            "starts_on",
            "ends_on",
            "city",
            "cover",
            "disciplines",
            "owner",
            "published_at",
            "created_at",
        ]


class ProjectWriteSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=180)
    description = serializers.CharField(max_length=20000)
    discipline_ids = serializers.PrimaryKeyRelatedField(
        queryset=Discipline.objects.filter(active=True), many=True
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(active=True), required=False, allow_null=True
    )
    starts_on = serializers.DateField(required=False, allow_null=True)
    ends_on = serializers.DateField(required=False, allow_null=True)
    is_commercial = serializers.BooleanField(default=False)
    cover_id = serializers.UUIDField(required=False, allow_null=True)
    visibility = serializers.ChoiceField(choices=Visibility.choices, default=Visibility.PUBLIC)

    def validate(self, attrs):
        starts, ends = attrs.get("starts_on"), attrs.get("ends_on")
        if starts and ends and ends < starts:
            raise serializers.ValidationError({"ends_on": "La fin doit suivre le début."})
        cover_id = attrs.pop("cover_id", None)
        if cover_id is not None:
            cover = MediaAsset.objects.filter(
                id=cover_id, owner=self.context["request"].user, mime_type__startswith="image/"
            ).first()
            if cover is None:
                raise serializers.ValidationError({"cover_id": "Image introuvable."})
            attrs["cover"] = cover
        elif "cover_id" in self.initial_data:
            attrs["cover"] = None
        return attrs


class TransitionSerializer(serializers.Serializer):
    status = serializers.CharField(max_length=20)
    reason = serializers.CharField(max_length=1000, required=False, allow_blank=True)


class InvitationCreateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=[ProjectMemberRole.MANAGER, ProjectMemberRole.MEMBER])
    email = serializers.EmailField(required=False, allow_blank=True, default="")


class InvitationSerializer(serializers.ModelSerializer):
    link_token = serializers.CharField(read_only=True, required=False)

    class Meta:
        model = ProjectInvitation
        fields = ["id", "role", "email", "expires_at", "accepted_at", "created_at", "link_token"]


class InvitationAcceptSerializer(serializers.Serializer):
    token = serializers.CharField()


class ProjectUpdateSerializer(serializers.ModelSerializer):
    author = OwnerSummarySerializer(read_only=True)
    media = MediaAssetSerializer(many=True, read_only=True)
    media_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False, default=list, max_length=4
    )

    class Meta:
        model = ProjectUpdate
        fields = ["id", "body", "author", "media", "media_ids", "created_at"]
        read_only_fields = ["id", "author", "created_at"]
