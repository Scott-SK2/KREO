from rest_framework import serializers

from .models import City, Discipline


class DisciplineSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    parent_slug = serializers.SlugRelatedField(source="parent", slug_field="slug", read_only=True)

    class Meta:
        model = Discipline
        fields = ["id", "slug", "label", "label_i18n", "parent_id", "parent_slug", "active"]

    def get_label(self, obj) -> str:
        return obj.label(self.context.get("locale", "fr"))


class CitySerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()

    class Meta:
        model = City
        fields = ["id", "country_code", "postal_code", "label", "label_i18n", "lat", "lng"]

    def get_label(self, obj) -> str:
        return obj.label(self.context.get("locale", "fr"))


class DisciplineAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discipline
        fields = ["id", "slug", "label_i18n", "parent", "active", "sort_order"]


class CityAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "country_code", "postal_code", "label_i18n", "lat", "lng", "active"]
