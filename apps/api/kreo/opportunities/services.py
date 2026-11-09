"""Cycle de vie des annonces et des rôles, règles de publication, refus automatique à la clôture."""

import logging

from django.db import transaction
from django.utils import timezone

from kreo.common.choices import (
    APPLICATION_OPEN_STATUSES,
    CompensationType,
    OpportunityStatus,
    ProjectStatus,
    RoleStatus,
)
from kreo.common.exceptions import BusinessRuleError
from kreo.common.permissions import ROLE_MANAGER, ROLE_MODERATOR, ROLE_OWNER
from kreo.common.transitions import StateMachine
from kreo.projects.permissions import project_roles

from .models import Opportunity, OpportunityRole

logger = logging.getLogger("kreo.opportunities")

OPPORTUNITY_MACHINE = (
    StateMachine("annonce")
    .add("draft", "open", {ROLE_OWNER, ROLE_MANAGER}, description="Publication")
    .add(
        "open",
        "closed",
        {ROLE_OWNER, ROLE_MANAGER, "system"},
        description="Porteur, échéance ou rôles pourvus",
    )
    .add(("draft", "open"), "cancelled", {ROLE_OWNER, ROLE_MANAGER, ROLE_MODERATOR})
)

FORBIDDEN_REQUIREMENT_KEYS = {
    "origin",
    "ethnicity",
    "religion",
    "health",
    "disability",
    "sexual_orientation",
    "measurements",
    "weight",
    "political",
    "union",
}
ALLOWED_REQUIREMENT_KEYS = {
    "playing_age_range",
    "languages",
    "skills",
    "voice_type",
    "instruments",
    "dance_styles",
    "costume_sizes",
    "driving_licence",
    "experience_level",
    "availability",
}


def _check_manager(actor, project):
    if not ({ROLE_OWNER, ROLE_MANAGER} & project_roles(actor, project)):
        raise BusinessRuleError("Seuls le porteur et les co-organisateurs gèrent les annonces.")


def validate_role_rules(*, project, compensation: str, requirements: dict) -> None:
    """Règles de publication : bénévole réservé au non commercial ; critères de la liste fermée."""
    if compensation == CompensationType.VOLUNTEER and project.is_commercial:
        raise BusinessRuleError(
            "Un rôle « bénévole » est refusé sur un projet commercial. "
            "Voir les règles belges sur le travail artistique.",
            problem_type="volunteer-on-commercial",
        )
    bad = set(requirements or {}) - ALLOWED_REQUIREMENT_KEYS
    if bad & FORBIDDEN_REQUIREMENT_KEYS:
        raise BusinessRuleError(
            "Critères interdits : origine, religion, santé, orientation, mensurations hors costume.",
            problem_type="forbidden-criteria",
        )
    if bad:
        raise BusinessRuleError(f"Critères hors liste fermée : {', '.join(sorted(bad))}.")


@transaction.atomic
def create_opportunity(
    *,
    project,
    actor,
    title,
    description,
    has_intimate_scene,
    roles: list[dict],
    template_discipline=None,
) -> Opportunity:
    _check_manager(actor, project)
    if not actor.is_phone_verified and not actor.is_staff:
        raise BusinessRuleError(
            "Confirme ton numéro de téléphone avant de publier une première annonce.",
            problem_type="phone-not-verified",
        )
    if project.status not in (ProjectStatus.DRAFT, ProjectStatus.PREPARING, ProjectStatus.ACTIVE):
        raise BusinessRuleError("Ce projet n'accepte plus d'annonces.")
    if not roles:
        raise BusinessRuleError("Une annonce contient au moins un rôle.")
    opportunity = Opportunity.objects.create(
        project=project,
        created_by=actor,
        title=title,
        description=description,
        has_intimate_scene=has_intimate_scene,
        template_discipline=template_discipline,
    )
    for role in roles:
        add_role(opportunity=opportunity, actor=actor, **role)
    return opportunity


def add_role(
    *,
    opportunity,
    actor,
    title,
    compensation,
    slots=1,
    description="",
    discipline=None,
    requirements=None,
    compensation_details="",
    city=None,
    deadline_at=None,
    beginner_friendly=False,
) -> OpportunityRole:
    _check_manager(actor, opportunity.project)
    if opportunity.status in (OpportunityStatus.CLOSED, OpportunityStatus.CANCELLED):
        raise BusinessRuleError("Cette annonce est fermée.")
    validate_role_rules(
        project=opportunity.project, compensation=compensation, requirements=requirements or {}
    )
    return OpportunityRole.objects.create(
        opportunity=opportunity,
        title=title,
        description=description,
        discipline=discipline,
        requirements=requirements or {},
        slots=slots,
        compensation=compensation,
        compensation_details=compensation_details,
        city=city,
        deadline_at=deadline_at,
        beginner_friendly=beginner_friendly,
    )


@transaction.atomic
def transition_opportunity(
    *, opportunity: Opportunity, target: str, actor, system: bool = False
) -> Opportunity:
    opportunity = (
        Opportunity.objects.select_for_update(of=("self",))
        .select_related("project")
        .get(pk=opportunity.pk)
    )
    roles = {"system"} if system else project_roles(actor, opportunity.project)
    OPPORTUNITY_MACHINE.check(opportunity.status, target, roles)
    now = timezone.now()

    if target == OpportunityStatus.OPEN:
        _check_publication_rules(opportunity)
        opportunity.published_at = now
        # Le projet brouillon devient visible avec sa première annonce.
        if opportunity.project.status == ProjectStatus.DRAFT:
            from kreo.projects.services import transition_project

            transition_project(
                project=opportunity.project, target=ProjectStatus.PREPARING, actor=actor
            )

    opportunity.status = target
    if target in (OpportunityStatus.CLOSED, OpportunityStatus.CANCELLED):
        opportunity.closed_at = now
    opportunity.save()

    if target in (OpportunityStatus.CLOSED, OpportunityStatus.CANCELLED):
        OpportunityRole.objects.filter(opportunity=opportunity).exclude(
            status=RoleStatus.CLOSED
        ).update(status=RoleStatus.CLOSED)
        from kreo.applications.services import auto_reject_open_applications

        auto_reject_open_applications(opportunity=opportunity, actor=actor)

    if actor is not None:
        from kreo.moderation.services import audit

        audit(
            actor,
            "opportunity.transition",
            target_type="opportunity",
            target_id=opportunity.id,
            to=target,
        )
    return opportunity


def _check_publication_rules(opportunity: Opportunity):
    roles = list(opportunity.roles.all())
    if not roles:
        raise BusinessRuleError("Ajoute au moins un rôle avant de publier.")
    if not opportunity.created_by.is_phone_verified and not opportunity.created_by.is_staff:
        raise BusinessRuleError(
            "Confirme ton numéro de téléphone avant de publier.", problem_type="phone-not-verified"
        )
    for role in roles:
        validate_role_rules(
            project=opportunity.project,
            compensation=role.compensation,
            requirements=role.requirements,
        )
    if opportunity.has_intimate_scene and opportunity.moderated_at is None:
        raise BusinessRuleError(
            "Une annonce avec scène de nu ou intime est vérifiée par un modérateur avant publication. "
            "Elle est en attente de validation.",
            problem_type="moderation-pending",
        )


@transaction.atomic
def close_role_if_filled(role: OpportunityRole) -> None:
    """Le rôle se ferme seul quand toutes ses places sont pourvues ; l'annonce quand tous les rôles le sont."""
    role = (
        OpportunityRole.objects.select_for_update(of=("self",))
        .select_related("opportunity")
        .get(pk=role.pk)
    )
    if role.status == RoleStatus.OPEN and role.accepted_count >= role.slots:
        role.status = RoleStatus.FILLED
        role.save(update_fields=["status"])
        from kreo.applications.services import auto_reject_open_applications

        auto_reject_open_applications(role=role, actor=None)
    opportunity = role.opportunity
    if (
        opportunity.status == OpportunityStatus.OPEN
        and not opportunity.roles.filter(status=RoleStatus.OPEN).exists()
    ):
        transition_opportunity(
            opportunity=opportunity, target=OpportunityStatus.CLOSED, actor=None, system=True
        )


@transaction.atomic
def close_role(*, role: OpportunityRole, actor) -> OpportunityRole:
    _check_manager(actor, role.opportunity.project)
    if role.status == RoleStatus.CLOSED:
        return role
    role.status = RoleStatus.CLOSED
    role.save(update_fields=["status"])
    from kreo.applications.services import auto_reject_open_applications

    auto_reject_open_applications(role=role, actor=actor)
    opportunity = role.opportunity
    if (
        opportunity.status == OpportunityStatus.OPEN
        and not opportunity.roles.filter(status=RoleStatus.OPEN).exists()
    ):
        transition_opportunity(
            opportunity=opportunity, target=OpportunityStatus.CLOSED, actor=None, system=True
        )
    return role


def close_all_for_project(*, project, actor, reason: str) -> None:
    for opportunity in project.opportunities.filter(
        status__in=[OpportunityStatus.DRAFT, OpportunityStatus.OPEN]
    ):
        target = (
            OpportunityStatus.CLOSED
            if opportunity.status == OpportunityStatus.OPEN
            else OpportunityStatus.CANCELLED
        )
        transition_opportunity(opportunity=opportunity, target=target, actor=None, system=True)


def has_open_applications(role):
    return role.applications.filter(status__in=APPLICATION_OPEN_STATUSES).exists()
