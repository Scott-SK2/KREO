"""Crédits : proposition par le porteur (projet terminé), confirmation, refus, contestation, arbitrage."""

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from kreo.common.choices import CreditStatus, ProjectStatus
from kreo.common.exceptions import BusinessRuleError, ConflictError
from kreo.common.permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_MODERATOR, ROLE_OWNER
from kreo.common.transitions import StateMachine
from kreo.notifications.services import notify
from kreo.projects.permissions import project_roles

from .models import CreditEvent, ProjectCredit

BENEFICIARY = "beneficiary"
C = CreditStatus


def _guard_reason(reason="", **_):
    if not reason or len(reason.strip()) < 10:
        raise BusinessRuleError("Un motif d'au moins 10 caractères est obligatoire pour contester.")


CREDIT_MACHINE = (
    StateMachine("crédit")
    .add((C.PROPOSED,), C.CONFIRMED, {BENEFICIARY, ROLE_MODERATOR, ROLE_ADMIN})
    .add((C.PROPOSED,), C.DECLINED, {BENEFICIARY, ROLE_MODERATOR, ROLE_ADMIN})
    .add((C.PROPOSED, C.CONFIRMED), C.DISPUTED, {BENEFICIARY}, guard=_guard_reason)
    .add(
        (C.DISPUTED,),
        C.PROPOSED,
        {ROLE_OWNER, ROLE_MANAGER},
        description="Après correction du rôle",
    )
    .add((C.DISPUTED,), C.CONFIRMED, {ROLE_MODERATOR, ROLE_ADMIN}, description="Arbitrage")
    .add((C.DISPUTED,), C.DECLINED, {ROLE_MODERATOR, ROLE_ADMIN}, description="Arbitrage")
)


def actor_roles_for(actor, credit) -> set[str]:
    roles = project_roles(actor, credit.project)
    if actor is not None and actor.is_authenticated and credit.user_id == actor.id:
        roles.add(BENEFICIARY)
    return roles


@transaction.atomic
def propose_credit(*, project, actor, role_name, user=None, email="") -> ProjectCredit:
    roles = project_roles(actor, project)
    if not ({ROLE_OWNER, ROLE_MANAGER} & roles):
        raise BusinessRuleError("Seuls le porteur et les co-organisateurs proposent des crédits.")
    if project.status not in (ProjectStatus.COMPLETED, ProjectStatus.ARCHIVED):
        raise BusinessRuleError(
            "Les crédits se proposent une fois le projet terminé.",
            problem_type="project-not-completed",
        )
    if user is None and not email:
        raise BusinessRuleError("Indique un membre ou un e-mail.")
    if user is not None and user.id == actor.id and project.owner_id == actor.id:
        # Le porteur peut se créditer lui-même ; il est alors bénéficiaire et confirme.
        pass
    from kreo.identity.models import User

    if user is None:
        existing_user = User.objects.alive().filter(email__iexact=email).first()
        if existing_user:
            user, email = existing_user, ""
    if (
        ProjectCredit.objects.filter(project=project, role_name__iexact=role_name)
        .filter(**({"user": user} if user else {"invited_email__iexact": email}))
        .exists()
    ):
        raise ConflictError("Ce crédit existe déjà.", problem_type="credit-exists")

    credit = ProjectCredit.objects.create(
        project=project,
        user=user,
        invited_email=email.lower(),
        role_name=role_name,
        proposed_by=actor,
    )
    CreditEvent.objects.create(credit=credit, actor=actor, to_status=C.PROPOSED)

    if user is not None:
        notify(
            event_key="credit.proposed",
            recipient=user,
            payload={
                "title": f"Crédit proposé : {role_name} sur « {project.title} »",
                "credit_id": str(credit.id),
            },
            dedup_key=f"credit.proposed:{credit.id}",
            deep_link=f"/compte/credits/{credit.id}",
        )
    else:
        from kreo.identity.tasks import send_external_email

        send_external_email.delay(
            email,
            "credit_proposed_external",
            {
                "project_title": project.title,
                "role_name": role_name,
                "link": f"{settings.SITE_URL}/inscription",
            },
        )
    return credit


@transaction.atomic
def transition_credit(
    *, credit: ProjectCredit, target: str, actor, reason: str = ""
) -> ProjectCredit:
    credit = (
        ProjectCredit.objects.select_for_update(of=("self",))
        .select_related("project__owner", "user")
        .get(pk=credit.pk)
    )
    roles = actor_roles_for(actor, credit)
    # Un porteur ne peut pas confirmer son propre crédit proposé à un tiers : seul le bénéficiaire confirme.
    CREDIT_MACHINE.check(credit.status, target, roles, reason=reason)
    credit.status = target
    if target == C.CONFIRMED:
        credit.confirmed_at = timezone.now()
    if target == C.DISPUTED:
        credit.dispute_reason = reason
    credit.save()
    CreditEvent.objects.create(credit=credit, actor=actor, to_status=target, reason=reason)

    if target in (C.CONFIRMED, C.DISPUTED, C.DECLINED):
        key = "credit.confirmed" if target == C.CONFIRMED else "credit.disputed"
        label = {"confirmed": "confirmé", "disputed": "contesté", "declined": "refusé"}[target]
        notify(
            event_key=key,
            recipient=credit.project.owner,
            payload={
                "title": f"Crédit {label} : {credit.role_name}",
                "credit_id": str(credit.id),
                "body": reason,
            },
            dedup_key=f"{key}:{credit.id}:{target}:{credit.updated_at.timestamp():.0f}",
            deep_link=f"/projets/{credit.project.slug}/credits",
        )
    if (
        actor is not None
        and (ROLE_MODERATOR in roles or ROLE_ADMIN in roles)
        and BENEFICIARY not in roles
    ):
        from kreo.moderation.services import audit

        audit(
            actor,
            "credit.arbitrated",
            target_type="credit",
            target_id=credit.id,
            reason=reason,
            to=target,
        )
    return credit


def activate_email_credits(user) -> int:
    """À l'inscription : les crédits proposés à cet e-mail deviennent les siens."""
    qs = ProjectCredit.objects.filter(user__isnull=True, invited_email__iexact=user.email)
    count = 0
    for credit in qs:
        credit.user = user
        credit.invited_email = ""
        credit.save(update_fields=["user", "invited_email"])
        notify(
            event_key="credit.proposed",
            recipient=user,
            payload={
                "title": f"Crédit proposé : {credit.role_name} sur « {credit.project.title} »",
                "credit_id": str(credit.id),
            },
            dedup_key=f"credit.proposed:{credit.id}",
            deep_link=f"/compte/credits/{credit.id}",
        )
        count += 1
    return count
