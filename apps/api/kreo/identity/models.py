import secrets
import string
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone

from kreo.common.choices import AccountStatus


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra):
        if not email:
            raise ValueError("L'e-mail est obligatoire.")
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra):
        extra.setdefault("is_staff", False)
        extra.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra)

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault("is_staff", True)
        extra.setdefault("is_superuser", True)
        extra.setdefault("is_moderator", True)
        extra.setdefault("email_verified_at", timezone.now())
        return self._create_user(email, password, **extra)

    def alive(self):
        return self.get_queryset().filter(deleted_at__isnull=True)


class User(AbstractBaseUser, PermissionsMixin):
    """Compte membre. Table `users` du schéma de référence (+ colonnes de sécurité)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=255, db_column="password_hash")
    status = models.CharField(
        max_length=20, choices=AccountStatus.choices, default=AccountStatus.ACTIVE
    )
    email_verified_at = models.DateTimeField(null=True, blank=True)
    phone_verified_at = models.DateTimeField(null=True, blank=True)
    # Numéro confirmé, jamais exposé par l'API publique.
    phone_number = models.CharField(max_length=32, blank=True, default="")
    locale = models.CharField(max_length=8, default="fr")
    is_staff = models.BooleanField(default=False)
    is_moderator = models.BooleanField(default=False)
    # Sécurité du compte
    failed_login_count = models.PositiveSmallIntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    token_version = models.PositiveIntegerField(default=1)
    # Consentements versionnés (fiche 27)
    terms_version = models.CharField(max_length=20, blank=True, default="")
    terms_accepted_at = models.DateTimeField(null=True, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: list[str] = []

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=Q(deleted_at__isnull=True),
                name="users_email_active",
            )
        ]

    def __str__(self):
        return str(self.id)

    @property
    def is_active(self):
        return self.status != AccountStatus.DELETED and self.deleted_at is None

    @property
    def is_email_verified(self):
        return self.email_verified_at is not None

    @property
    def is_phone_verified(self):
        return self.phone_verified_at is not None

    @property
    def is_locked(self):
        return self.locked_until is not None and self.locked_until > timezone.now()

    def register_failed_login(self):
        self.failed_login_count += 1
        if self.failed_login_count >= settings.LOGIN_MAX_FAILURES:
            self.locked_until = timezone.now() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)
            self.failed_login_count = 0
        self.save(update_fields=["failed_login_count", "locked_until"])

    def reset_failed_logins(self):
        if self.failed_login_count or self.locked_until:
            self.failed_login_count = 0
            self.locked_until = None
            self.save(update_fields=["failed_login_count", "locked_until"])

    def revoke_all_sessions(self):
        """Déconnexion de tous les appareils : invalide tous les jetons émis."""
        self.token_version += 1
        self.save(update_fields=["token_version"])


def _invitation_code():
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(8))


def _default_invitation_expiry():
    return timezone.now() + timedelta(days=settings.BETA_INVITATION_VALIDITY_DAYS)


class BetaInvitation(models.Model):
    """Code d'invitation de la bêta fermée (5 par membre)."""

    code = models.CharField(max_length=16, primary_key=True, default=_invitation_code)
    inviter = models.ForeignKey(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="invitations_sent"
    )
    used_by = models.OneToOneField(
        User, null=True, blank=True, on_delete=models.SET_NULL, related_name="invitation_used"
    )
    expires_at = models.DateTimeField(default=_default_invitation_expiry)
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "beta_invitations"

    def __str__(self):
        return self.code

    @property
    def is_usable(self):
        return self.used_at is None and self.expires_at > timezone.now()


class OneTimeToken(models.Model):
    """Jetons à usage unique (vérification e-mail, réinitialisation, téléphone). Hachés."""

    class Purpose(models.TextChoices):
        EMAIL_VERIFICATION = "email_verification"
        PASSWORD_RESET = "password_reset"
        PHONE_VERIFICATION = "phone_verification"

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="one_time_tokens")
    purpose = models.CharField(max_length=30, choices=Purpose.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    payload = models.JSONField(default=dict, blank=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "one_time_tokens"
        indexes = [models.Index(fields=["user", "purpose"], name="idx_ott_user_purpose")]

    @property
    def is_valid(self):
        return self.used_at is None and self.expires_at > timezone.now()
