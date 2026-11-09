from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken


class CookieOrHeaderJWTAuthentication(JWTAuthentication):
    """
    Web : jeton d'accès dans un cookie HttpOnly. Mobile : en-tête Authorization: Bearer.
    Le claim `tv` (token_version) permet la déconnexion de tous les appareils.
    """

    def authenticate(self, request):
        header = self.get_header(request)
        raw_token = None
        if header is not None:
            raw_token = self.get_raw_token(header)
        if raw_token is None:
            raw_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        if raw_token is None:
            return None
        validated = self.get_validated_token(raw_token)
        user = self.get_user(validated)
        if validated.get("tv") != user.token_version:
            raise InvalidToken("Session révoquée.")
        if not user.is_active:
            raise AuthenticationFailed("Compte inactif.", code="user_inactive")
        return user, validated


class CookieOrHeaderJWTScheme(OpenApiAuthenticationExtension):
    target_class = "kreo.identity.authentication.CookieOrHeaderJWTAuthentication"
    name = "jwtAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Web : cookie HttpOnly `kreo_access` posé par /auth/login. Mobile : en-tête Authorization: Bearer.",
        }
