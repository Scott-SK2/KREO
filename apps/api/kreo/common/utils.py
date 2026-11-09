import hashlib
import hmac
import secrets

from django.conf import settings
from django.utils.text import slugify


def generate_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def hash_token(token: str) -> str:
    """Hachage HMAC-SHA256 des jetons stockés (vérification e-mail, invitations)."""
    return hmac.new(settings.SECRET_KEY.encode(), token.encode(), hashlib.sha256).hexdigest()


def unique_slug(model, base: str, *, field: str = "slug", max_length: int = 80) -> str:
    base_slug = slugify(base)[: max_length - 7] or "kreo"
    slug = base_slug
    while model.objects.filter(**{field: slug}).exists():
        slug = f"{base_slug}-{secrets.token_hex(3)}"
    return slug


def i18n_label(label_i18n: dict, locale: str = "fr") -> str:
    return label_i18n.get(locale) or label_i18n.get("fr") or next(iter(label_i18n.values()), "")
