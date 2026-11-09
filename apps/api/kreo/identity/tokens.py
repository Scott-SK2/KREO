from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken


def issue_tokens(user) -> dict:
    refresh = RefreshToken.for_user(user)
    refresh["tv"] = user.token_version
    access = refresh.access_token
    access["tv"] = user.token_version
    return {"access": str(access), "refresh": str(refresh)}


def set_auth_cookies(response, tokens: dict):
    common = {
        "httponly": True,
        "secure": settings.AUTH_COOKIE_SECURE,
        "samesite": settings.AUTH_COOKIE_SAMESITE,
        "domain": settings.AUTH_COOKIE_DOMAIN,
    }
    response.set_cookie(
        settings.AUTH_COOKIE_ACCESS,
        tokens["access"],
        max_age=int(settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()),
        path="/",
        **common,
    )
    response.set_cookie(
        settings.AUTH_COOKIE_REFRESH,
        tokens["refresh"],
        max_age=int(settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()),
        path="/api/v1/auth",
        **common,
    )


def clear_auth_cookies(response):
    response.delete_cookie(
        settings.AUTH_COOKIE_ACCESS, path="/", domain=settings.AUTH_COOKIE_DOMAIN
    )
    response.delete_cookie(
        settings.AUTH_COOKIE_REFRESH, path="/api/v1/auth", domain=settings.AUTH_COOKIE_DOMAIN
    )
