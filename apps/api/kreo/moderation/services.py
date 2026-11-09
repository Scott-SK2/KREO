import logging

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from kreo.common.choices import ReportPriority, ReportStatus
from kreo.common.exceptions import BusinessRuleError, ConflictError
from kreo.notifications.services import notify

from .models import Appeal, AuditLog, Block, ModerationAction, Report

logger = logging.getLogger("kreo.moderation")

PERSON_SAFETY_REASONS = {"harassment", "threats", "minor_safety", "sexual_content", "scam_money"}


def audit(
    actor, action: str, *, target_type: str = "", target_id=None, reason: str = "", **metadata
):
    AuditLog.objects.create(
        actor=actor,
        action=action,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        metadata=metadata,
    )


def is_blocked_between(a, b) -> bool:
    if a is None or b is None:
        return False
    return Block.objects.filter(Q(blocker=a, blocked=b) | Q(blocker=b, blocked=a)).exists()


def blocked_user_ids(user) -> set:
    """Identifiants à exclure des résultats pour `user` (dans les deux sens)."""
    if user is None or not user.is_authenticated:
        return set()
    made = Block.objects.filter(blocker=user).values_list("blocked_id", flat=True)
    received = Block.objects.filter(blocked=user).values_list("blocker_id", flat=True)
    return set(made) | set(received)


def block_user(blocker, blocked) -> Block:
    if blocker.id == blocked.id:
        raise BusinessRuleError("Tu ne peux pas te bloquer toi-même.")
    block, _ = Block.objects.get_or_create(blocker=blocker, blocked=blocked)
    return block


def create_report(*, reporter, target_type, target_id, reason, details="") -> Report:
    priority = (
        ReportPriority.PERSON_SAFETY if reason in PERSON_SAFETY_REASONS else ReportPriority.STANDARD
    )
    existing = Report.objects.filter(
        reporter=reporter, target_type=target_type, target_id=target_id, status=ReportStatus.OPEN
    ).first()
    if existing:
        return existing
    return Report.objects.create(
        reporter=reporter,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        priority=priority,
        details=details,
    )


def _resolve_affected_user(target_type, target_id):
    from kreo.applications.models import Application
    from kreo.identity.models import User
    from kreo.messaging.models import Message
    from kreo.opportunities.models import Opportunity
    from kreo.projects.models import Project, ProjectUpdate

    lookups = {
        "user": lambda: User.objects.filter(id=target_id).first(),
        "project": lambda: getattr(Project.objects.filter(id=target_id).first(), "owner", None),
        "opportunity": lambda: getattr(
            Opportunity.objects.select_related("project").filter(id=target_id).first(),
            "created_by",
            None,
        ),
        "project_update": lambda: getattr(
            ProjectUpdate.objects.filter(id=target_id).first(), "author", None
        ),
        "message": lambda: getattr(Message.objects.filter(id=target_id).first(), "sender", None),
        "application": lambda: getattr(
            Application.objects.filter(id=target_id).first(), "applicant", None
        ),
    }
    fn = lookups.get(target_type)
    return fn() if fn else None


@transaction.atomic
def take_action(
    *, moderator, report: Report | None, target_type, target_id, action, statement_of_reasons
) -> ModerationAction:
    """Applique une action, la journalise et envoie la motivation à la personne concernée."""
    from kreo.identity.models import User
    from kreo.messaging.models import Message
    from kreo.opportunities.models import Opportunity
    from kreo.projects.models import Project, ProjectUpdate

    if len(statement_of_reasons.strip()) < 20:
        raise BusinessRuleError("La motivation doit faire au moins 20 caractères (DSA).")

    affected = _resolve_affected_user(target_type, target_id)
    now = timezone.now()

    if action == ModerationAction.Action.REMOVE_CONTENT:
        if target_type == "project_update":
            ProjectUpdate.objects.filter(id=target_id).update(deleted_at=now)
        elif target_type == "message":
            Message.objects.filter(id=target_id).update(deleted_at=now)
        elif target_type == "opportunity":
            Opportunity.objects.filter(id=target_id).update(status="cancelled", updated_at=now)
        elif target_type == "project":
            Project.objects.filter(id=target_id).update(visibility="private", updated_at=now)
    elif action == ModerationAction.Action.SUSPEND_ACCOUNT:
        if affected is None:
            raise BusinessRuleError("Aucun compte à suspendre pour cette cible.")
        User.objects.filter(id=affected.id).update(status="suspended")
        affected.revoke_all_sessions()
    elif action == ModerationAction.Action.REINSTATE_ACCOUNT:
        if affected is None:
            raise BusinessRuleError("Aucun compte à rétablir.")
        User.objects.filter(id=affected.id).update(status="active")
    elif action == ModerationAction.Action.APPROVE_OPPORTUNITY:
        Opportunity.objects.filter(id=target_id).update(moderated_at=now)
    elif action == ModerationAction.Action.REJECT_OPPORTUNITY:
        Opportunity.objects.filter(id=target_id).update(status="cancelled", moderated_at=now)

    record = ModerationAction.objects.create(
        report=report,
        moderator=moderator,
        target_type=target_type,
        target_id=target_id,
        affected_user=affected,
        action=action,
        statement_of_reasons=statement_of_reasons,
    )
    if report is not None:
        report.status = (
            ReportStatus.DISMISSED
            if action == ModerationAction.Action.DISMISS
            else ReportStatus.ACTIONED
        )
        report.save(update_fields=["status", "updated_at"])

    audit(
        moderator,
        f"moderation.{action}",
        target_type=target_type,
        target_id=target_id,
        reason="",
        report_id=str(report.id) if report else None,
    )

    if affected is not None and action != ModerationAction.Action.DISMISS:
        notify(
            event_key="moderation.decision",
            recipient=affected,
            payload={
                "title": "Décision de modération",
                "body": statement_of_reasons,
                "action": action,
                "appeal_possible": settings.FEATURES["appeals"],
            },
            dedup_key=f"moderation.decision:{record.id}",
            deep_link=f"/compte/moderation/{record.id}",
        )
    return record


@transaction.atomic
def file_appeal(*, appellant, action: ModerationAction, body: str) -> Appeal:
    if not settings.FEATURES["appeals"]:
        raise BusinessRuleError(
            "Les recours ouvrent au lancement public.", problem_type="feature-disabled"
        )
    if action.affected_user_id != appellant.id:
        raise BusinessRuleError("Seule la personne concernée peut faire un recours.")
    if (timezone.now() - action.created_at).days > 30:
        raise BusinessRuleError("Le délai de recours de 30 jours est dépassé.")
    if Appeal.objects.filter(action=action, status="open").exists():
        raise ConflictError("Un recours est déjà en cours pour cette décision.")
    return Appeal.objects.create(action=action, appellant=appellant, body=body)


@transaction.atomic
def decide_appeal(*, moderator, appeal: Appeal, upheld: bool, reasons: str) -> Appeal:
    if appeal.action.moderator_id == moderator.id:
        raise BusinessRuleError("Un recours est traité par un autre modérateur.")
    appeal.status = "upheld" if upheld else "reversed"
    appeal.decided_by = moderator
    appeal.decision_reasons = reasons
    appeal.decided_at = timezone.now()
    appeal.save()
    if not upheld and appeal.action.action == ModerationAction.Action.SUSPEND_ACCOUNT:
        from kreo.identity.models import User

        User.objects.filter(id=appeal.appellant_id).update(status="active")
    audit(moderator, "moderation.appeal_decided", target_type="appeal", target_id=appeal.id)
    notify(
        event_key="moderation.appeal_decided",
        recipient=appeal.appellant,
        payload={"title": "Réponse à ton recours", "body": reasons, "status": appeal.status},
        dedup_key=f"appeal.decided:{appeal.id}",
        deep_link=f"/compte/moderation/{appeal.action_id}",
    )
    return appeal
