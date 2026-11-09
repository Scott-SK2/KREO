"""
Réglages communs. Les secrets viennent de l'environnement (django-environ), jamais du dépôt.
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:3000"]),
    FEATURE_SOCIAL=(bool, False),
    FEATURE_PUSH=(bool, False),
    FEATURE_SAVED_SEARCHES=(bool, False),
    FEATURE_APPEALS=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env("ALLOWED_HOSTS")

SITE_URL = env("SITE_URL", default="http://localhost:3000")
API_URL = env("API_URL", default="http://localhost:8000")

# ---------------------------------------------------------------------------
# Applications : monolithe modulaire (identity, profiles, projects, opportunities,
# applications, messaging, credits, notifications, moderation).
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    # Tiers
    "rest_framework",
    "django_filters",
    "corsheaders",
    "drf_spectacular",
    # KREO
    "kreo.common",
    "kreo.identity",
    "kreo.referentials",
    "kreo.media",
    "kreo.profiles",
    "kreo.projects",
    "kreo.opportunities",
    "kreo.applications",
    "kreo.messaging",
    "kreo.credits",
    "kreo.social",
    "kreo.notifications",
    "kreo.moderation",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "kreo.common.middleware.RequestIdMiddleware",
]

ROOT_URLCONF = "kreo.urls"
WSGI_APPLICATION = "kreo.wsgi.application"
ASGI_APPLICATION = "kreo.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "kreo" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ---------------------------------------------------------------------------
# Base de données : PostgreSQL 16 (french + unaccent + pg_trgm)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://kreo:kreo@localhost:5432/kreo"),
}
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        "KEY_PREFIX": "kreo",
    }
}

# ---------------------------------------------------------------------------
# Identité : utilisateur personnalisé, Argon2
# ---------------------------------------------------------------------------
AUTH_USER_MODEL = "identity.User"
# L'unicité de l'e-mail est garantie par un index partiel (comptes non supprimés), voir identity.User.
SILENCED_SYSTEM_CHECKS = ["auth.E003"]
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Règles d'accès et d'abus (cahier des charges)
BETA_INVITATIONS_PER_MEMBER = 5
BETA_INVITATION_VALIDITY_DAYS = 30
EMAIL_VERIFICATION_VALIDITY_HOURS = 24
PASSWORD_RESET_VALIDITY_HOURS = 2
PROJECT_INVITATION_VALIDITY_DAYS = 7
LOGIN_MAX_FAILURES = 5
LOGIN_LOCKOUT_MINUTES = 15
ACCOUNT_PURGE_AFTER_DAYS = 30
MINIMUM_AGE = 18
MEDIA_MAX_BYTES = 10 * 1024 * 1024
MEDIA_QUOTA_BYTES_PER_ACCOUNT = 200 * 1024 * 1024
MEDIA_ALLOWED_MIME_TYPES = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
MEDIA_SIGNED_URL_TTL_SECONDS = 5 * 60
PROJECT_UPDATE_MAX_PHOTOS = 4
QUIET_HOURS = (22, 8)  # heure de Bruxelles : pas de notification (sauf messages)

FEATURES = {
    "social": env("FEATURE_SOCIAL"),
    "push": env("FEATURE_PUSH"),
    "saved_searches": env("FEATURE_SAVED_SEARCHES"),
    "appeals": env("FEATURE_APPEALS"),
}

# ---------------------------------------------------------------------------
# API REST
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "kreo.identity.authentication.CookieOrHeaderJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_PAGINATION_CLASS": "kreo.common.pagination.CreatedAtCursorPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "EXCEPTION_HANDLER": "kreo.common.exceptions.problem_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
        "auth": "10/min",
        "auth_ip": "30/min",
        "applications_daily": "20/day",
        "opportunities_daily": "5/day",
        "messages": "60/min",
        "reports": "30/day",
    },
    "DATETIME_FORMAT": "iso-8601",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "sub",
    "TOKEN_OBTAIN_SERIALIZER": "kreo.identity.serializers.LoginSerializer",
}
AUTH_COOKIE_ACCESS = "kreo_access"
AUTH_COOKIE_REFRESH = "kreo_refresh"
AUTH_COOKIE_SECURE = not DEBUG
AUTH_COOKIE_SAMESITE = "Lax"
AUTH_COOKIE_DOMAIN = env("AUTH_COOKIE_DOMAIN", default=None)

SPECTACULAR_SETTINGS = {
    "TITLE": "KREO API",
    "DESCRIPTION": (
        "API REST de KREO — Une idée, des talents, un projet. "
        "Identifiants UUID, dates ISO 8601 en UTC, pagination par curseur, "
        "erreurs au format application/problem+json."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "COMPONENT_SPLIT_REQUEST": True,
    "OAS_VERSION": "3.1.0",
    "ENUM_NAME_OVERRIDES": {
        "ProjectStatusEnum": "kreo.common.choices.ProjectStatus",
        "OpportunityStatusEnum": "kreo.common.choices.OpportunityStatus",
        "RoleStatusEnum": "kreo.common.choices.RoleStatus",
        "ApplicationStatusEnum": "kreo.common.choices.ApplicationStatus",
        "CreditStatusEnum": "kreo.common.choices.CreditStatus",
        "VisibilityEnum": "kreo.common.choices.Visibility",
        "CompensationTypeEnum": "kreo.common.choices.CompensationType",
        "ReportTargetTypeEnum": "kreo.common.choices.ReportTargetType",
        "FavoriteTargetTypeEnum": "kreo.common.choices.FavoriteTargetType",
        "ReportStatusEnum": "kreo.common.choices.ReportStatus",
        "AppealStatusEnum": "kreo.common.choices.AppealStatus",
        "ProjectMemberRoleEnum": "kreo.common.choices.ProjectMemberRole",
        "InvitationRoleEnum": [("manager", "manager"), ("member", "member")],
    },
}

CORS_ALLOWED_ORIGINS = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = CORS_ALLOWED_ORIGINS

# ---------------------------------------------------------------------------
# Internationalisation : FR en V1, clés i18n, NL puis EN
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "fr-be"
LANGUAGES = [("fr", "Français"), ("nl", "Nederlands"), ("en", "English")]
TIME_ZONE = "UTC"
DISPLAY_TIME_ZONE = "Europe/Brussels"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------------------------------------------------------
# E-mail (fournisseur transactionnel UE en prod), Celery, journaux
# ---------------------------------------------------------------------------
EMAIL_CONFIG = env.email("EMAIL_URL", default="consolemail://")
vars().update(EMAIL_CONFIG)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="KREO <bonjour@kreo.local>")

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = None
CELERY_TASK_ALWAYS_EAGER = False
CELERY_TASK_ACKS_LATE = True
CELERY_TIMEZONE = "Europe/Brussels"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "kreo.common.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "json"},
    },
    "root": {"handlers": ["console"], "level": "INFO"},
    "loggers": {
        "django.request": {"level": "WARNING"},
        "kreo": {"level": "INFO"},
    },
}

SENTRY_DSN = env("SENTRY_DSN", default="")
