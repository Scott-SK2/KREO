"""Cycle de vie des candidatures : candidature en un clic, suivi, offre, acceptation, refus automatique."""

import logging

from django.db import transaction
from django.utils import timezone

from kreo.common.choices import (
    APPLICATION_OPEN_STATUSES,
    ApplicationStatus,
    ProjectMemberRole,
    RoleStatus,
)
from kreo.common.exceptions import BusinessRuleError, ConflictError
from kreo.common.permissions import ROLE_MANAGER, ROLE_OWNER
from kreo.common.transitions import StateMachine
from kreo.moderation.services import is_blocked_between
from kreo.notifications.services import notify
from kreo.projects.permissions import project_roles

from .models import Application, ApplicationAttachment, ApplicationEvent

logger = logging.getLogger("kreo.applications")

CANDIDATE = "candidate"
MANAGERS = {ROLE_OWNER, ROLE_MANAGER}
S = ApplicationStatus


def _guard_slot_free(application=None, **_):
    role = application.role
    if (
        role.accepted_count
        + role.applications.filter(status=S.OFFERED).exclude(pk=application.pk).count()
        >= role.slots
    ):
        raise ConflictError(
            "Toutes les places de ce rôle sont déjà pourvues ou offertes.", problem_type="role-full"
        )


APPLICATION_MACHINE = (
    StateMachine("candidature")
    .add(
        (S.SUBMITTED,),
        S.VIEWED,
        MANAGERS | {"system"},
        description="Automatique à la première ouverture",
    )
    .add((S.SUBMITTED, S.VIEWED), S.SHORTLISTED, MANAGERS)
    .add((S.SHORTLISTED,), S.AUDITION, MANAGERS)
    .add(
        (S.SUBMITTED, S.VIEWED, S.SHORTLISTED, S.AUDITION),
        S.OFFERED,
        MANAGERS,
        guard=_guard_slot_free,
    )
    .add((S.OFFERED,), S.ACCEPTED, {CANDIDATE}, description="Crée le membre d'équipe")
    .add((S.OFFERED,), S.DECLINED, {CANDIDATE})
    .add((S.SUBMITTED, S.VIEWED, S.SHORTLISTED, S.AUDITION), S.REJECTED, MANAGERS | {"system"})
    .add((S.SUBMITTED, S.VIEWED, S.SHORTLISTED, S.AUDITION, S.OFFERED), S.WITHDRAWN, {CANDIDATE})
)

COURTEOUS_REJECTION = (
    "Merci pour ta candidature. Le rôle est maintenant pourvu ou l'annonce est fermée. "
    "D'autres projets t'attendent sur KREO."
)


def actor_roles_for(actor, application) -> set[str]:
    roles = project_roles(actor, application.role.opportunity.project)
    if actor is not None and actor.is_authenticated and actor.id == application.applicant_id:
        roles.add(CANDIDATE)
    return roles


def can_view_application(actor, application) -> bool:
    roles = actor_roles_for(actor, application)
    return bool(roles & (MANAGERS | {CANDIDATE}))


@transaction.atomic
def apply(
    *,
    role,
    applicant,
    message="",
    availability_confirmed=None,
    portfolio_media_ids=(),
    attachment_ids=(),
) -> Application:
    role = (
        type(role)
        .objects.select_for_update(of=("self",))
        .select_related("opportunity__project__owner")
        .get(pk=role.pk)
    )
    project = role.opportunity.project
    if applicant.status != "active":
        raise BusinessRuleError(
            "Un compte suspendu ne peut pas postuler.", problem_type="account-suspended"
        )
    if not role.is_open:
        raise BusinessRuleError(
            "Ce rôle ne reçoit plus de candidature (fermé, expiré ou complet).",
            problem_type="role-closed",
        )
    if role.deadline_at and role.deadline_at < timezone.now():
        raise BusinessRuleError("L'échéance de ce rôle est dépassée.", problem_type="role-closed")
    if MANAGERS & project_roles(applicant, project):
        raise BusinessRuleError("Tu ne peux pas candidater à ton propre projet.")
    if is_blocked_between(applicant, project.owner):
        raise BusinessRuleError("Tu ne peux pas candidater à ce projet.", problem_type="blocked")
    if Application.objects.filter(role=role, applicant=applicant).exists():
        raise ConflictError("Tu as déjà candidaté à ce rôle.", problem_type="already-applied")

    from kreo.media.models import MediaAsset

    application = Application.objects.create(
        role=role,
        applicant=applicant,
        message=message,
        availability_confirmed=availability_confirmed,
    )
    if portfolio_media_ids:
        application.portfolio_media.set(
            MediaAsset.objects.filter(id__in=portfolio_media_ids, owner=applicant)
        )
    for asset in MediaAsset.objects.filter(id__in=attachment_ids, owner=applicant)[:3]:
        ApplicationAttachment.objects.create(application=application, media=asset)
    ApplicationEvent.objects.create(
        application=application, actor=applicant, from_status=None, to_status=S.SUBMITTED
    )

    recipients = {project.owner} | {
        m.user
        for m in project.memberships.filter(role=ProjectMemberRole.MANAGER).select_related("user")
    }
    for recipient in recipients:
        notify(
            event_key="application.new",
            recipient=recipient,
            payload={
                "title": f"Nouvelle candidature : {role.title}",
                "application_id": str(application.id),
                "role_id": str(role.id),
            },
            dedup_key=f"application.new:{application.id}:{recipient.id}",
            deep_link=f"/tableau-de-bord/candidats/{application.id}",
        )
    return application


CANDIDATE_NOTIFICATIONS = {
    S.VIEWED: ("application.viewed", "Ta candidature a été vue"),
    S.SHORTLISTED: ("application.shortlisted", "Tu es présélectionné·e"),
    S.AUDITION: ("application.audition", "Tu es invité·e à une audition"),
    S.OFFERED: ("application.offered", "Tu as reçu une offre"),
    S.REJECTED: ("application.rejected", "Candidature non retenue"),
}


@transaction.atomic
def transition_application(
    *, application: Application, target: str, actor, note: str = "", system: bool = False
) -> Application:
    application = (
        Application.objects.select_for_update(of=("self",))
        .select_related("role__opportunity__project__owner", "applicant")
        .get(pk=application.pk)
    )
    roles = {"system"} if system else actor_roles_for(actor, application)
    APPLICATION_MACHINE.check(application.status, target, roles, application=application)
    previous = application.status
    role = application.role
    now = timezone.now()

    if target == S.OFFERED and role.status != RoleStatus.OPEN:
        raise ConflictError("Ce rôle n'est plus ouvert.", problem_type="role-closed")

    application.status = target
    if (
        previous == S.SUBMITTED
        and target != S.WITHDRAWN
        and application.first_response_at is None
        and not system
    ):
        application.first_response_at = now
    application.save()
    ApplicationEvent.objects.create(
        application=application,
        actor=None if system else actor,
        from_status=previous,
        to_status=target,
        note=note,
    )

    project = role.opportunity.project
    if target == S.ACCEPTED:
        from kreo.projects.models import ProjectMember

        ProjectMember.objects.get_or_create(
            project=project,
            user=application.applicant,
            defaults={"role": ProjectMemberRole.MEMBER, "role_title": role.title},
        )
        from kreo.opportunities.services import close_role_if_filled

        close_role_if_filled(role)

    # Notifications
    if target in CANDIDATE_NOTIFICATIONS:
        key, title = CANDIDATE_NOTIFICATIONS[target]
        notify(
            event_key=key,
            recipient=application.applicant,
            payload={
                "title": f"{title} — {role.title}",
                "application_id": str(application.id),
                "body": note or (COURTEOUS_REJECTION if target == S.REJECTED else ""),
            },
            dedup_key=f"{key}:{application.id}",
            deep_link=f"/mes-candidatures/{application.id}",
        )
    if target in (S.ACCEPTED, S.DECLINED):
        key = "application.accepted" if target == S.ACCEPTED else "application.declined"
        recipients = {project.owner} | {
            m.user
            for m in project.memberships.filter(role=ProjectMemberRole.MANAGER).select_related(
                "user"
            )
        }
        for recipient in recipients:
            notify(
                event_key=key,
                recipient=recipient,
                payload={
                    "title": f"Offre {'acceptée' if target == S.ACCEPTED else 'déclinée'} : {role.title}",
                    "application_id": str(application.id),
                },
                dedup_key=f"{key}:{application.id}:{recipient.id}",
                deep_link=f"/tableau-de-bord/candidats/{application.id}",
            )
    return application


def mark_viewed(application: Application, actor) -> Application:
    """Passage automatique en « viewed » à la première ouverture par un responsable."""
    if application.status == S.SUBMITTED and (MANAGERS & actor_roles_for(actor, application)):
        return transition_application(application=application, target=S.VIEWED, actor=actor)
    return application


def auto_reject_open_applications(*, opportunity=None, role=None, actor=None) -> int:
    """À la clôture, chaque candidature encore ouverte reçoit un seul refus courtois."""
    qs = Application.objects.filter(status__in=APPLICATION_OPEN_STATUSES).exclude(status=S.OFFERED)
    if opportunity is not None:
        qs = qs.filter(role__opportunity=opportunity)
    if role is not None:
        qs = qs.filter(role=role)
    count = 0
    for application in qs.select_related("role__opportunity__project"):
        transition_application(
            application=application,
            target=S.REJECTED,
            actor=actor,
            note=COURTEOUS_REJECTION,
            system=True,
        )
        count += 1
    if count:
        logger.info(
            "auto rejections", extra={"event": "applications_auto_rejected", "duration_ms": count}
        )
    return count
