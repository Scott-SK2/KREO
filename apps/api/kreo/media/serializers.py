from rest_framework import serializers

from kreo.common.choices import Visibility

from .models import MediaAsset
from .services import asset_urls


class MediaUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    alt_text = serializers.CharField(max_length=300, required=False, allow_blank=True, default="")
    visibility = serializers.ChoiceField(choices=Visibility.choices, default=Visibility.PRIVATE)


class MediaAssetSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    variants = serializers.SerializerMethodField()

    class Meta:
        model = MediaAsset
        fields = [
            "id",
            "mime_type",
            "size_bytes",
            "width",
            "height",
            "alt_text",
            "scan_status",
            "visibility",
            "url",
            "variants",
            "created_at",
        ]

    def get_url(self, obj) -> str | None:
        urls = asset_urls(obj)
        return urls["url"] if urls else None

    def get_variants(self, obj) -> dict:
        urls = asset_urls(obj)
        return urls["variants"] if urls else {}
