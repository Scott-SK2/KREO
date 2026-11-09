from django.conf import settings
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from kreo.common.permissions import IsAdmin
from kreo.common.throttles import AuthAnonThrottle, AuthUserThrottle

from . import serializers, services
from .export import build_account_export
from .models import BetaInvitation, User
from .tokens import clear_auth_cookies, issue_tokens, set_auth_cookies

AUTH_TAG = ["Authentification"]
ACCOUNT_TAG = ["Compte"]


def _wants_cookies(request) -> bool:
    """Le web reçoit des cookies HttpOnly ; le mobile demande les jetons dans le corps."""
    return request.headers.get("X-Client", "web") != "mobile"


def _auth_response(request, user, status_code=status.HTTP_200_OK):
    tokens = issue_tokens(user)
    data = {"user": serializers.MeSerializer(user, context={"request": request}).data}
    if _wants_cookies(request):
        response = Response(data, status=status_code)
        set_auth_cookies(response, tokens)
        return response
    return Response({**data, **tokens}, status=status_code)


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Créer un compte avec un code d'invitation",
        request=serializers.RegisterSerializer,
        responses={
            201: serializers.MeSerializer,
            422: OpenApiResponse(description="Code invalide"),
        },
    )
    def post(self, request):
        ser = serializers.RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = services.register(**ser.validated_data)
        return Response(
            serializers.MeSerializer(user, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Confirmer l'adresse e-mail (lien valable 24 h)",
        request=serializers.EmailTokenSerializer,
        responses={200: serializers.MeSerializer},
    )
    def post(self, request):
        ser = serializers.EmailTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = services.verify_email(ser.validated_data["token"])
        return _auth_response(request, user)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Renvoyer le lien de vérification",
        request=serializers.EmailSerializer,
        responses={202: None},
    )
    def post(self, request):
        ser = serializers.EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = (
            User.objects.alive()
            .filter(email__iexact=ser.validated_data["email"], email_verified_at__isnull=True)
            .first()
        )
        if user:
            services.send_email_verification(user)
        return Response(status=status.HTTP_202_ACCEPTED)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Se connecter",
        description="Web : cookies HttpOnly. Mobile (en-tête X-Client: mobile) : jetons dans la réponse.",
        request=serializers.LoginSerializer,
        responses={200: serializers.MeSerializer},
    )
    def post(self, request):
        ser = serializers.LoginSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = services.login(request=request, **ser.validated_data)
        return _auth_response(request, user)


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Renouveler le jeton d'accès (rotation du refresh)",
        request=serializers.RefreshSerializer,
        responses={200: serializers.TokenPairSerializer},
    )
    def post(self, request):
        raw = request.data.get("refresh") or request.COOKIES.get(settings.AUTH_COOKIE_REFRESH)
        if not raw:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        try:
            old = RefreshToken(raw)
            user = User.objects.alive().get(id=old["sub"])
            if old.get("tv") != user.token_version or not user.is_active:
                raise TokenError("révoqué")
        except (TokenError, User.DoesNotExist, KeyError):
            response = Response(
                {
                    "type": "https://kreo.be/problems/token-invalid",
                    "title": "Session expirée",
                    "status": 401,
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )
            clear_auth_cookies(response)
            return response
        tokens = issue_tokens(user)
        if _wants_cookies(request):
            response = Response({"ok": True})
            set_auth_cookies(response, tokens)
            return response
        return Response(tokens)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Se déconnecter (option : de tous les appareils)",
        request={
            "application/json": {
                "type": "object",
                "properties": {"all_devices": {"type": "boolean"}},
            }
        },
        responses={204: None},
    )
    def post(self, request):
        if request.data.get("all_devices"):
            request.user.revoke_all_sessions()
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Demander une réinitialisation de mot de passe",
        request=serializers.EmailSerializer,
        responses={202: None},
    )
    def post(self, request):
        ser = serializers.EmailSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.request_password_reset(ser.validated_data["email"])
        return Response(status=status.HTTP_202_ACCEPTED)


class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [AuthAnonThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Choisir un nouveau mot de passe",
        request=serializers.PasswordResetConfirmSerializer,
        responses={204: None},
    )
    def post(self, request):
        ser = serializers.PasswordResetConfirmSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        services.confirm_password_reset(ser.validated_data["token"], ser.validated_data["password"])
        return Response(status=status.HTTP_204_NO_CONTENT)


class PhoneVerifyView(APIView):
    """POST /auth/phone/verify : étape 1 avec phone_number, étape 2 avec code."""

    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AuthUserThrottle]

    @extend_schema(
        tags=AUTH_TAG,
        summary="Vérifier le numéro de téléphone (porteur vérifié)",
        request=serializers.PhoneStartSerializer,
        responses={200: serializers.MeSerializer, 202: None},
    )
    def post(self, request):
        if "code" in request.data:
            ser = serializers.PhoneConfirmSerializer(data=request.data)
            ser.is_valid(raise_exception=True)
            user = services.confirm_phone_verification(request.user, ser.validated_data["code"])
            return Response(serializers.MeSerializer(user, context={"request": request}).data)
        ser = serializers.PhoneStartSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        code = services.start_phone_verification(request.user, ser.validated_data["phone_number"])
        body = {}
        if getattr(settings, "PHONE_VERIFICATION_DEBUG_RETURN_CODE", False):
            body["debug_code"] = code
        return Response(body, status=status.HTTP_202_ACCEPTED)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        tags=ACCOUNT_TAG, summary="Mon compte", responses={200: serializers.MeSerializer}
    )
    def get(self, request):
        return Response(serializers.MeSerializer(request.user, context={"request": request}).data)

    @extend_schema(
        tags=ACCOUNT_TAG,
        summary="Modifier mon compte",
        request=serializers.MeUpdateSerializer,
        responses={200: serializers.MeSerializer},
    )
    def patch(self, request):
        ser = serializers.MeUpdateSerializer(request.user, data=request.data, partial=True)
        ser.is_valid(raise_exception=True)
        ser.save()
        return Response(serializers.MeSerializer(request.user, context={"request": request}).data)

    @extend_schema(
        tags=ACCOUNT_TAG,
        summary="Supprimer mon compte (anonymisation immédiate, effacement sous 30 jours)",
        responses={204: None},
    )
    def delete(self, request):
        services.delete_account(request.user)
        response = Response(status=status.HTTP_204_NO_CONTENT)
        clear_auth_cookies(response)
        return response


class MeExportView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [AuthUserThrottle]

    @extend_schema(tags=ACCOUNT_TAG, summary="Exporter mes données (JSON)", responses={200: dict})
    def get(self, request):
        data = build_account_export(request.user)
        response = Response(data)
        response["Content-Disposition"] = (
            f'attachment; filename="kreo-export-{timezone.now():%Y%m%d}.json"'
        )
        return response


class MyInvitationsView(generics.ListAPIView):
    """Les 5 codes d'invitation du membre (bêta fermée)."""

    serializer_class = serializers.BetaInvitationSerializer
    pagination_class = None
    queryset = BetaInvitation.objects.none()

    @extend_schema(tags=ACCOUNT_TAG, summary="Mes codes d'invitation")
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return BetaInvitation.objects.none()
        return BetaInvitation.objects.filter(inviter=self.request.user).order_by("created_at")


class AdminInvitationsView(APIView):
    permission_classes = [IsAdmin]

    @extend_schema(
        tags=["Back-office"],
        summary="Lister les invitations bêta",
        responses={200: serializers.BetaInvitationSerializer(many=True)},
    )
    def get(self, request):
        qs = BetaInvitation.objects.order_by("-created_at")[:500]
        return Response(serializers.BetaInvitationSerializer(qs, many=True).data)

    @extend_schema(
        tags=["Back-office"],
        summary="Générer des invitations bêta",
        request=serializers.AdminInvitationCreateSerializer,
        responses={201: serializers.BetaInvitationSerializer(many=True)},
    )
    @transaction.atomic
    def post(self, request):
        ser = serializers.AdminInvitationCreateSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        kwargs = {"inviter": request.user}
        if ser.validated_data.get("validity_days"):
            from datetime import timedelta

            kwargs["expires_at"] = timezone.now() + timedelta(
                days=ser.validated_data["validity_days"]
            )
        created = BetaInvitation.objects.bulk_create(
            [BetaInvitation(**kwargs) for _ in range(ser.validated_data["count"])]
        )
        return Response(serializers.BetaInvitationSerializer(created, many=True).data, status=201)
