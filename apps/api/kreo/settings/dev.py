from .base import *  # noqa: F403

DEBUG = True
AUTH_COOKIE_SECURE = False
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
# Le code de vérification du téléphone est écrit dans la réponse en dev (pas de SMS).
PHONE_VERIFICATION_DEBUG_RETURN_CODE = True
