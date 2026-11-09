"""Services métier d'identité : inscription sur invitation, vérification, connexion, suppression."""

import secrets
from datetime import date, timedelta

from django.conf import settings
from django.contrib.auth import authenticate
from django.db import transaction
from django.utils import timezone
from rest_framework import exceptions

from kreo.common.exceptions import BusinessRuleError, ConflictError
from kreo.common.utils import generate_token, hash_token

from . import tasks
from .models import BetaInvitation, OneTimeToken, User


def _age(birth_date: date) -> int:
    today = timezone.localdate()
    return (
        today.year
        - birth_date.year
        - ((today.month, today.day) < (birth_date.month, birth_date.day))
    )


@transaction.atomic
def register(
    *,
    email: str,
    password: str,
    invitation_code: str,
    birth_date: date,
    terms_version: str,
    locale: str = "fr",
) -> User:
    code = invitation_code.strip().upper()
    invitation = BetaInvitation.objects.select_for_update().filter(code=code).first()
    if invitation is None or not invitation.is_usable:
        raise BusinessRuleError(
            "Ce code d'invitation est invalide, déjà utilisé ou expiré.",
            problem_type="invitation-invalid",
        )
    if _age(birth_date) < settings.MINIMUM_AGE:
        raise BusinessRuleError(
            "KREO est réservé aux personnes majeures en V1.", problem_type="minimum-age"
        )
    if User.objects.alive().filter(email__iexact=email).exists():
        raise ConflictError("Un compte existe déjà avec cet e-mail.", problem_type="email-taken")

    user = User.objects.create_user(
        email=email,
        password=password,
        birth_date=birth_date,
        locale=locale,
        terms_version=terms_version,
        terms_accepted_at=timezone.now(),
    )
    invitation.used_by = user
    invitation.used_at = timezone.now()
    invitation.save(update_fields=["used_by", "used_at"])

    # Chaque membre reçoit ses propres invitations à partager.
    BetaInvitation.objects.bulk_create(
        [BetaInvitation(inviter=user) for _ in range(settings.BETA_INVITATIONS_PER_MEMBER)]
    )
    send_email_verification(user)
    return user


def _create_one_time_token(user, purpose, validity: timedelta, payload=None) -> str:
    OneTimeToken.objects.filter(user=user, purpose=purpose, used_at__isnull=True).update(
        used_at=timezone.now()
    )
    raw = generate_token()
    OneTimeToken.objects.create(
        user=user,
        purpose=purpose,
        token_hash=hash_token(raw),
        payload=payload or {},
        expires_at=timezone.now() + validity,
    )
    return raw


def _consume_one_time_token(raw: str, purpose) -> OneTimeToken:
    token = (
        OneTimeToken.objects.select_for_update()
        .select_related("user")
        .filter(token_hash=hash_token(raw), purpose=purpose)
        .first()
    )
    if token is None or not token.is_valid:
        raise BusinessRuleError("Ce lien est invalide ou a expiré.", problem_type="token-invalid")
    token.used_at = timezone.now()
    token.save(update_fields=["used_at"])
    return token


def send_email_verification(user: User) -> None:
    raw = _create_one_time_token(
        user,
        OneTimeToken.Purpose.EMAIL_VERIFICATION,
        timedelta(hours=settings.EMAIL_VERIFICATION_VALIDITY_HOURS),
    )
    link = f"{settings.SITE_URL}/verifier-email?token={raw}"
    tasks.send_transactional_email.delay(
        str(user.id),
        "email_verification",
        {"link": link, "hours": settings.EMAIL_VERIFICATION_VALIDITY_HOURS},
    )


@transaction.atomic
def verify_email(raw_token: str) -> User:
    token = _consume_one_time_token(raw_token, OneTimeToken.Purpose.EMAIL_VERIFICATION)
    user = token.user
    if user.email_verified_at is None:
        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at"])
        # Un crédit proposé à cet e-mail avant l'inscription s'active maintenant.
        from kreo.credits.services import activate_email_credits

        activate_email_credits(user)
    return user


def login(*, request, email: str, password: str) -> User:
    user = User.objects.alive().filter(email__iexact=email).first()
    generic = exceptions.AuthenticationFailed("E-mail ou mot de passe incorrect.")
    if user is None:
        raise generic
    if user.is_locked:
        raise exceptions.AuthenticationFailed(
            "Trop de tentatives. Réessaie dans quelques minutes.", code="account_locked"
        )
    authenticated = authenticate(request, username=user.email, password=password)
    if authenticated is None:
        user.register_failed_login()
        raise generic
    if user.status == "deleted":
        raise generic
    if not user.is_email_verified:
        raise exceptions.AuthenticationFailed(
            "Confirme d'abord ton adresse e-mail.", code="email_not_verified"
        )
    user.reset_failed_logins()
    return user


def request_password_reset(email: str) -> None:
    user = User.objects.alive().filter(email__iexact=email).first()
    if user is None:
        return  # réponse identique pour ne pas révéler l'existence du compte
    raw = _create_one_time_token(
        user,
        OneTimeToken.Purpose.PASSWORD_RESET,
        timedelta(hours=settings.PASSWORD_RESET_VALIDITY_HOURS),
    )
    link = f"{settings.SITE_URL}/reinitialiser-mot-de-passe?token={raw}"
    tasks.send_transactional_email.delay(str(user.id), "password_reset", {"link": link})


@transaction.atomic
def confirm_password_reset(raw_token: str, new_password: str) -> User:
    token = _consume_one_time_token(raw_token, OneTimeToken.Purpose.PASSWORD_RESET)
    user = token.user
    user.set_password(new_password)
    user.revoke_all_sessions()
    user.save(update_fields=["password"])
    return user


def start_phone_verification(user: User, phone_number: str) -> str:
    code = f"{secrets.randbelow(10**6):06d}"
    _create_one_time_token(
        user,
        OneTimeToken.Purpose.PHONE_VERIFICATION,
        timedelta(minutes=10),
        payload={"phone_number": phone_number},
    )
    # Le jeton stocké est le hachage du code ; on remplace le hachage aléatoire.
    OneTimeToken.objects.filter(
        user=user, purpose=OneTimeToken.Purpose.PHONE_VERIFICATION, used_at__isnull=True
    ).update(token_hash=hash_token(f"{user.id}:{code}"))
    tasks.send_sms_code.delay(str(user.id), phone_number, code)
    return code


@transaction.atomic
def confirm_phone_verification(user: User, code: str) -> User:
    token = (
        OneTimeToken.objects.select_for_update()
        .filter(
            user=user,
            purpose=OneTimeToken.Purpose.PHONE_VERIFICATION,
            token_hash=hash_token(f"{user.id}:{code.strip()}"),
        )
        .first()
    )
    if token is None or not token.is_valid:
        raise BusinessRuleError("Code incorrect ou expiré.", problem_type="token-invalid")
    token.used_at = timezone.now()
    token.save(update_fields=["used_at"])
    user.phone_number = token.payload.get("phone_number", "")
    user.phone_verified_at = timezone.now()
    user.save(update_fields=["phone_number", "phone_verified_at"])
    return user


@transaction.atomic
def delete_account(user: User) -> None:
    """Anonymisation immédiate ; effacement définitif sous 30 jours (tâche planifiée)."""
    from kreo.profiles.models import ArtistProfile

    now = timezone.now()
    user.status = "deleted"
    user.deleted_at = now
    user.email = f"deleted+{user.id}@kreo.invalid"
    user.phone_number = ""
    user.phone_verified_at = None
    user.set_unusable_password()
    user.revoke_all_sessions()
    user.save()
    ArtistProfile.objects.filter(user=user).update(
        display_name="Compte supprimé", bio="", avatar=None, visibility="private"
    )
    OneTimeToken.objects.filter(user=user).delete()
    tasks.export_or_purge_notice.delay(str(user.id))
