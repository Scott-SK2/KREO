from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import BetaInvitation, User


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)
    invitation_code = serializers.CharField(max_length=16)
    birth_date = serializers.DateField()
    terms_version = serializers.CharField(max_length=20)
    locale = serializers.ChoiceField(choices=[c for c, _ in settings.LANGUAGES], default="fr")

    def validate_password(self, value):
        validate_password(value)
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class TokenPairSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()


class RefreshSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=False, allow_blank=True)


class EmailTokenSerializer(serializers.Serializer):
    token = serializers.CharField()


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(write_only=True, min_length=10, max_length=128)

    def validate_password(self, value):
        validate_password(value)
        return value


class PhoneStartSerializer(serializers.Serializer):
    phone_number = serializers.RegexField(
        r"^\+[1-9]\d{7,14}$", help_text="Format E.164, par exemple +32470000000."
    )


class PhoneConfirmSerializer(serializers.Serializer):
    code = serializers.RegexField(r"^\d{6}$")


class MeSerializer(serializers.ModelSerializer):
    email_verified = serializers.BooleanField(source="is_email_verified", read_only=True)
    phone_verified = serializers.BooleanField(source="is_phone_verified", read_only=True)
    roles = serializers.SerializerMethodField()
    profile_slug = serializers.SerializerMethodField()
    invitations_left = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "status",
            "locale",
            "email_verified",
            "phone_verified",
            "roles",
            "profile_slug",
            "invitations_left",
            "terms_version",
            "created_at",
        ]
        read_only_fields = [f for f in fields if f not in ("locale",)]

    def get_roles(self, user) -> list[str]:
        from kreo.common.permissions import global_roles

        return sorted(global_roles(user))

    def get_profile_slug(self, user) -> str | None:
        profile = getattr(user, "profile", None)
        return profile.slug if profile else None

    def get_invitations_left(self, user) -> int:
        return BetaInvitation.objects.filter(inviter=user, used_at__isnull=True).count()


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["locale"]


class BetaInvitationSerializer(serializers.ModelSerializer):
    used = serializers.SerializerMethodField()

    class Meta:
        model = BetaInvitation
        fields = ["code", "expires_at", "used", "created_at"]

    def get_used(self, obj) -> bool:
        return obj.used_at is not None


class AdminInvitationCreateSerializer(serializers.Serializer):
    count = serializers.IntegerField(min_value=1, max_value=200, default=1)
    validity_days = serializers.IntegerField(min_value=1, max_value=365, required=False)
