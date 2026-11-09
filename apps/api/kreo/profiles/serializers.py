import re

from django.utils import timezone
from rest_framework import serializers

from kreo.common.choices import CASTING_ATTRIBUTE_KEYS, Visibility
from kreo.media.serializers import MediaAssetSerializer
from kreo.referentials.models import City, Discipline
from kreo.referentials.serializers import CitySerializer, DisciplineSerializer

from .models import ArtistProfile, ProfileAttribute

VIDEO_HOSTS = re.compile(r"^https://(www\.)?(youtube\.com|youtu\.be|vimeo\.com)/", re.I)


class ProfileAttributeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileAttribute
        fields = ["attribute_key", "value_json", "visibility"]

    def validate_attribute_key(self, value):
        if value not in CASTING_ATTRIBUTE_KEYS:
            raise serializers.ValidationError(
                "Attribut hors liste fermée. Autorisés : "
                + ", ".join(sorted(CASTING_ATTRIBUTE_KEYS))
            )
        return value


class PublicProfileSerializer(serializers.ModelSerializer):
    """Vue publique : pas d'e-mail, pas de téléphone, attributs privés masqués."""

    disciplines = DisciplineSerializer(many=True, read_only=True)
    city = CitySerializer(read_only=True)
    avatar = MediaAssetSerializer(read_only=True)
    gallery = serializers.SerializerMethodField()
    attributes = serializers.SerializerMethodField()
    is_verified_owner = serializers.SerializerMethodField()

    class Meta:
        model = ArtistProfile
        fields = [
            "slug",
            "display_name",
            "bio",
            "city",
            "avatar",
            "visibility",
            "experience_level",
            "video_links",
            "external_links",
            "open_to_beginner_roles",
            "disciplines",
            "gallery",
            "attributes",
            "is_verified_owner",
            "created_at",
        ]

    def get_gallery(self, obj) -> list:
        return MediaAssetSerializer(
            [pm.media for pm in obj.profilemedia_set.select_related("media")], many=True
        ).data

    def get_attributes(self, obj) -> list:
        return ProfileAttributeSerializer(
            obj.attributes.filter(visibility=Visibility.PUBLIC), many=True
        ).data

    def get_is_verified_owner(self, obj) -> bool:
        return obj.user.phone_verified_at is not None


class MyProfileSerializer(PublicProfileSerializer):
    discipline_ids = serializers.PrimaryKeyRelatedField(
        queryset=Discipline.objects.filter(active=True), many=True, write_only=True, required=False
    )
    city_id = serializers.PrimaryKeyRelatedField(
        queryset=City.objects.filter(active=True),
        source="city",
        write_only=True,
        required=False,
        allow_null=True,
    )
    avatar_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    attributes = ProfileAttributeSerializer(many=True, required=False)
    completion = serializers.SerializerMethodField()

    class Meta(PublicProfileSerializer.Meta):
        fields = PublicProfileSerializer.Meta.fields + [
            "discipline_ids",
            "city_id",
            "avatar_id",
            "completion",
            "onboarding_completed_at",
        ]
        read_only_fields = ["slug", "created_at", "onboarding_completed_at"]

    def get_completion(self, obj) -> dict:
        return obj.completion

    def validate_video_links(self, links):
        if len(links) > 10:
            raise serializers.ValidationError("10 liens vidéo maximum.")
        for link in links:
            if not isinstance(link, str) or not VIDEO_HOSTS.match(link):
                raise serializers.ValidationError("Seuls les liens YouTube et Vimeo sont acceptés.")
        return links

    def validate_external_links(self, links):
        if len(links) > 10:
            raise serializers.ValidationError("10 liens maximum.")
        for link in links:
            if not isinstance(link, str) or not link.startswith("https://"):
                raise serializers.ValidationError("Les liens doivent commencer par https://.")
        return links

    def validate_discipline_ids(self, value):
        if value is not None and len(value) < 2:
            raise serializers.ValidationError("Choisis au moins deux disciplines.")
        if len(value) > 8:
            raise serializers.ValidationError("Huit disciplines maximum.")
        return value

    def validate_avatar_id(self, value):
        if value is None:
            return None
        from kreo.media.models import MediaAsset

        asset = MediaAsset.objects.filter(id=value, owner=self.context["request"].user).first()
        if asset is None or not asset.is_image:
            raise serializers.ValidationError("Image introuvable ou non autorisée.")
        return asset

    def update(self, instance, validated):
        disciplines = validated.pop("discipline_ids", None)
        attributes = validated.pop("attributes", None)
        if "avatar_id" in validated:
            instance.avatar = validated.pop("avatar_id")
        for field, value in validated.items():
            setattr(instance, field, value)
        instance.save()
        if disciplines is not None:
            instance.disciplines.set(disciplines)
        if attributes is not None:
            instance.attributes.all().delete()
            ProfileAttribute.objects.bulk_create(
                [ProfileAttribute(profile=instance, **attr) for attr in attributes]
            )
        if (
            instance.onboarding_completed_at is None
            and instance.city_id
            and instance.disciplines.count() >= 2
        ):
            instance.onboarding_completed_at = timezone.now()
            instance.save(update_fields=["onboarding_completed_at"])
        return instance


class ProfileMediaOrderSerializer(serializers.Serializer):
    media_ids = serializers.ListField(child=serializers.UUIDField(), max_length=24)
