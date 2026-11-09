from django.conf import settings
from django.db import models

from kreo.common.models import UUIDPrimaryKeyModel


class Conversation(UUIDPrimaryKeyModel):
    """Conversation privée liée à une candidature (porteur/co-orga ↔ candidat)."""

    application = models.OneToOneField(
        "applications.Application", on_delete=models.CASCADE, related_name="conversation"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_message_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversations"


class ConversationParticipant(models.Model):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="participants"
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="conversations"
    )
    last_read_at = models.DateTimeField(null=True, blank=True)
    safety_tips_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "conversation_participants"
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "user"], name="uq_conversation_participant"
            )
        ]


class Message(UUIDPrimaryKeyModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="messages_sent"
    )
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "-created_at"], name="idx_messages_conv_time")
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(body=""), name="message_body_not_empty")
        ]
