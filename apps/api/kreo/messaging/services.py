from django.db import transaction
from django.utils import timezone

from kreo.common.choices import ProjectMemberRole
from kreo.common.exceptions import BusinessRuleError
from kreo.moderation.services import is_blocked_between
from kreo.notifications.services import notify
from kreo.projects.permissions import is_project_manager

from .models import Conversation, ConversationParticipant, Message

SAFETY_TIPS = [
    "Rencontre dans un lieu public ou professionnel.",
    "Ne paie jamais pour une audition, un casting ou un rôle.",
    "Signale toute demande déplacée depuis la conversation.",
]


@transaction.atomic
def get_or_create_conversation(*, application, actor) -> Conversation:
    """Le porteur n'écrit qu'aux candidats de ses projets ; le candidat qu'au porteur de sa candidature."""
    project = application.role.opportunity.project
    is_candidate = actor.id == application.applicant_id
    if not is_candidate and not is_project_manager(actor, project):
        raise BusinessRuleError("Tu ne peux écrire qu'aux candidats de tes projets.")
    if is_blocked_between(actor, project.owner if is_candidate else application.applicant):
        raise BusinessRuleError("Cette conversation n'est pas disponible.", problem_type="blocked")
    conversation, created = Conversation.objects.get_or_create(application=application)
    if created:
        participants = {application.applicant, project.owner} | {
            m.user
            for m in project.memberships.filter(role=ProjectMemberRole.MANAGER).select_related(
                "user"
            )
        }
        ConversationParticipant.objects.bulk_create(
            [ConversationParticipant(conversation=conversation, user=u) for u in participants]
        )
    return conversation


def is_participant(user, conversation) -> bool:
    return ConversationParticipant.objects.filter(conversation=conversation, user=user).exists()


@transaction.atomic
def send_message(*, conversation: Conversation, sender, body: str) -> Message:
    body = body.strip()
    if not body:
        raise BusinessRuleError("Le message est vide.")
    if len(body) > 5000:
        raise BusinessRuleError("5 000 caractères maximum.")
    if sender.status != "active":
        raise BusinessRuleError(
            "Un compte suspendu ne peut pas envoyer de message.", problem_type="account-suspended"
        )
    participant = (
        ConversationParticipant.objects.select_for_update()
        .filter(conversation=conversation, user=sender)
        .first()
    )
    if participant is None:
        raise BusinessRuleError("Tu ne participes pas à cette conversation.")
    others = [p.user for p in conversation.participants.exclude(user=sender).select_related("user")]
    for other in others:
        if is_blocked_between(sender, other):
            raise BusinessRuleError(
                "Cette conversation est coupée par un blocage.", problem_type="blocked"
            )

    message = Message.objects.create(conversation=conversation, sender=sender, body=body)
    now = timezone.now()
    conversation.last_message_at = now
    conversation.save(update_fields=["last_message_at"])
    participant.last_read_at = now
    if participant.safety_tips_seen_at is None:
        participant.safety_tips_seen_at = now
    participant.save(update_fields=["last_read_at", "safety_tips_seen_at"])

    sender_name = getattr(getattr(sender, "profile", None), "display_name", "Un membre")
    for other in others:
        notify(
            event_key="message.new",
            recipient=other,
            payload={
                "title": f"Nouveau message de {sender_name}",
                "conversation_id": str(conversation.id),
            },
            dedup_key=f"message.new:{message.id}:{other.id}",
            deep_link=f"/messages/{conversation.id}",
        )
    return message


def mark_read(*, conversation, user) -> None:
    ConversationParticipant.objects.filter(conversation=conversation, user=user).update(
        last_read_at=timezone.now()
    )
    from kreo.notifications.models import Notification

    Notification.objects.filter(
        recipient=user,
        event_key="message.new",
        read_at__isnull=True,
        payload__conversation_id=str(conversation.id),
    ).update(read_at=timezone.now())
