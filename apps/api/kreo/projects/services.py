"""Services métier des projets : création, cycle de vie, équipe, invitations, actualités."""

from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from kreo.common.choices import ProjectMemberRole, ProjectStatus
from kreo.common.exceptions import BusinessRuleError
from kreo.common.permissions import ROLE_ADMIN, ROLE_MANAGER, ROLE_OWNER
from kreo.common.transitions import StateMachine
from kreo.common.utils import generate_token, hash_token, unique_slug
from kreo.notifications.services import notify

from .models import Project, ProjectInvitation, ProjectMember, ProjectUpdate, ProjectUpdateMedia
from .permissions import project_roles

PROJECT_MACHINE = (
    StateMachine("projet")
    .add(
        "draft", "preparing", {ROLE_OWNER, ROLE_MANAGER}, description="Projet visible publiquement"
    )
    .add("draft", "active", {ROLE_OWNER, ROLE_MANAGER}, description="Projet visible publiquement")
    .add("preparing", "active", {ROLE_OWNER, ROLE_MANAGER})
    .add("active", "completed", {ROLE_OWNER}, description="Ouvre les crédits ; ferme les annonces")
    .add(
        ("draft", "preparing", "active"),
        "cancelled",
        {ROLE_OWNER},
        description="Ferme les annonces",
    )
    .add(
        ("completed", "cancelled"),
        "archived",
        {ROLE_OWNER, ROLE_ADMIN},
        description="Lecture seule",
    )
)


@transaction.atomic
def create_project(
    *,
    owner,
    title,
    description,
    disciplines,
    city=None,
    starts_on=None,
    ends_on=None,
    is_commercial=False,
    cover=None,
    visibility="public",
) -> Project:
    if not owner.is_phone_verified and not owner.is_staff:
        raise BusinessRuleError(
            "Confirme ton numéro de téléphone avant de créer un projet (porteur vérifié).",
            problem_type="phone-not-verified",
        )
    if len(disciplines) < 1:
        raise BusinessRuleError("Choisis au moins une discipline.")
    project = Project.objects.create(
        owner=owner,
        slug=unique_slug(Project, title, max_length=120),
        title=title,
        description=description,
        city=city,
        starts_on=starts_on,
        ends_on=ends_on,
        is_commercial=is_commercial,
        cover=cover,
        visibility=visibility,
    )
    project.disciplines.set(disciplines)
    ProjectMember.objects.create(project=project, user=owner, role=ProjectMemberRole.OWNER)
    return project


@transaction.atomic
def transition_project(*, project: Project, target: str, actor) -> Project:
    project = Project.objects.select_for_update(of=("self",)).get(pk=project.pk)
    roles = project_roles(actor, project)
    PROJECT_MACHINE.check(project.status, target, roles)
    now = timezone.now()
    previous = project.status
    project.status = target
    if target in (ProjectStatus.PREPARING, ProjectStatus.ACTIVE) and project.published_at is None:
        project.published_at = now
    if target == ProjectStatus.COMPLETED:
        project.completed_at = now
    project.save()

    if target in (ProjectStatus.COMPLETED, ProjectStatus.CANCELLED):
        from kreo.opportunities.services import close_all_for_project

        close_all_for_project(project=project, actor=actor, reason=target)

    from kreo.moderation.services import audit

    audit(
        actor,
        "project.transition",
        target_type="project",
        target_id=project.id,
        metadata_from=previous,
        metadata_to=target,
    )
    return project


def _check_manager(actor, project):
    if not ({ROLE_OWNER, ROLE_MANAGER} & project_roles(actor, project)):
        raise BusinessRuleError("Seuls le porteur et les co-organisateurs peuvent faire cela.")


@transaction.atomic
def invite(*, project: Project, actor, role: str, email: str = "") -> tuple[ProjectInvitation, str]:
    """Le porteur invite un co-organisateur ; porteur et co-orga peuvent inviter un membre."""
    roles = project_roles(actor, project)
    if role == ProjectMemberRole.MANAGER and not ({ROLE_OWNER, ROLE_ADMIN} & roles):
        raise BusinessRuleError("Seul le porteur peut inviter un co-organisateur.")
    if role == ProjectMemberRole.MEMBER:
        _check_manager(actor, project)
    if project.status in (ProjectStatus.ARCHIVED, ProjectStatus.CANCELLED):
        raise BusinessRuleError("Ce projet est clos.")
    raw = generate_token()
    invitation = ProjectInvitation.objects.create(
        project=project,
        invited_by=actor,
        email=email.lower() if email else "",
        role=role,
        token_hash=hash_token(raw),
        expires_at=timezone.now() + timedelta(days=settings.PROJECT_INVITATION_VALIDITY_DAYS),
    )
    if email:
        from kreo.identity.models import User

        recipient = User.objects.alive().filter(email__iexact=email).first()
        link = f"/projets/{project.slug}/rejoindre?token={raw}"
        if recipient is not None:
            notify(
                event_key="project.invitation",
                recipient=recipient,
                payload={
                    "title": f"Invitation à rejoindre « {project.title} »",
                    "body": f"On te propose de devenir {'co-organisateur·rice' if role == 'manager' else 'membre'} du projet.",
                    "project_id": str(project.id),
                },
                dedup_key=f"project.invitation:{invitation.id}",
                deep_link=link,
            )
        else:
            from kreo.identity.tasks import send_external_email

            # Personne non inscrite : e-mail d'invitation à créer un compte puis rejoindre.
            send_external_email.delay(
                email,
                "project_invitation_external",
                {"link": f"{settings.SITE_URL}{link}", "project_title": project.title},
            )
    return invitation, raw


@transaction.atomic
def accept_invitation(*, raw_token: str, user) -> ProjectMember:
    invitation = (
        ProjectInvitation.objects.select_for_update(of=("self",))
        .select_related("project")
        .filter(token_hash=hash_token(raw_token))
        .first()
    )
    if invitation is None or invitation.accepted_at or invitation.expires_at < timezone.now():
        raise BusinessRuleError(
            "Cette invitation est invalide ou a expiré.", problem_type="invitation-invalid"
        )
    if invitation.email and invitation.email != user.email.lower():
        raise BusinessRuleError(
            "Cette invitation a été envoyée à une autre adresse.",
            problem_type="invitation-mismatch",
        )
    project = invitation.project
    if project.owner_id == user.id:
        raise BusinessRuleError("Tu es déjà porteur de ce projet.")
    member, created = ProjectMember.objects.get_or_create(
        project=project, user=user, defaults={"role": invitation.role}
    )
    if (
        not created
        and invitation.role == ProjectMemberRole.MANAGER
        and member.role == ProjectMemberRole.MEMBER
    ):
        member.role = ProjectMemberRole.MANAGER
        member.save(update_fields=["role"])
    invitation.accepted_at = timezone.now()
    invitation.accepted_by = user
    invitation.save(update_fields=["accepted_at", "accepted_by"])
    return member


@transaction.atomic
def remove_member(*, project: Project, actor, user_id) -> None:
    """Retrait immédiat. Seul le porteur retire un co-organisateur ; le membre peut partir seul."""
    roles = project_roles(actor, project)
    member = ProjectMember.objects.filter(project=project, user_id=user_id).first()
    if member is None:
        raise BusinessRuleError("Cette personne ne fait pas partie de l'équipe.")
    if member.role == ProjectMemberRole.OWNER:
        raise BusinessRuleError("Le porteur ne peut pas être retiré de son projet.")
    if str(actor.id) == str(user_id):
        member.delete()
        return
    if member.role == ProjectMemberRole.MANAGER and not ({ROLE_OWNER, ROLE_ADMIN} & roles):
        raise BusinessRuleError("Seul le porteur peut retirer un co-organisateur.")
    if member.role == ProjectMemberRole.MEMBER and not (
        {ROLE_OWNER, ROLE_MANAGER, ROLE_ADMIN} & roles
    ):
        raise BusinessRuleError("Action réservée au porteur et aux co-organisateurs.")
    member.delete()


@transaction.atomic
def post_update(*, project: Project, actor, body: str, media_ids: list) -> ProjectUpdate:
    _check_manager(actor, project)
    if project.status == ProjectStatus.ARCHIVED:
        raise BusinessRuleError("Un projet archivé est en lecture seule.")
    if len(media_ids) > settings.PROJECT_UPDATE_MAX_PHOTOS:
        raise BusinessRuleError("Quatre photos maximum par actualité.")
    from kreo.media.models import MediaAsset

    assets = list(
        MediaAsset.objects.filter(id__in=media_ids, owner=actor, mime_type__startswith="image/")
    )
    update = ProjectUpdate.objects.create(project=project, author=actor, body=body)
    ProjectUpdateMedia.objects.bulk_create(
        [ProjectUpdateMedia(update=update, media=a, sort_order=i) for i, a in enumerate(assets)]
    )
    return update
