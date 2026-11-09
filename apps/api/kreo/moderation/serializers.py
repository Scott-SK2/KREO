from rest_framework import serializers

from kreo.common.choices import ReportTargetType

from .models import Appeal, AuditLog, Block, ModerationAction, Report

REPORT_REASONS = [
    "harassment",
    "threats",
    "minor_safety",
    "sexual_content",
    "scam_money",
    "discrimination",
    "spam",
    "fake_casting",
    "private_audition",
    "inappropriate",
    "other",
]


class ReportCreateSerializer(serializers.Serializer):
    target_type = serializers.ChoiceField(choices=ReportTargetType.choices)
    target_id = serializers.UUIDField()
    reason = serializers.ChoiceField(choices=REPORT_REASONS)
    details = serializers.CharField(max_length=2000, required=False, allow_blank=True, default="")


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = [
            "id",
            "target_type",
            "target_id",
            "reason",
            "priority",
            "details",
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
        ]


class BlockCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()


class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = ["id", "blocked", "created_at"]


class ModerationActionCreateSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=ModerationAction.Action.choices)
    statement_of_reasons = serializers.CharField(min_length=20, max_length=4000)


class ModerationActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModerationAction
        fields = [
            "id",
            "report",
            "moderator",
            "target_type",
            "target_id",
            "affected_user",
            "action",
            "statement_of_reasons",
            "created_at",
        ]


class AppealCreateSerializer(serializers.Serializer):
    action_id = serializers.UUIDField()
    body = serializers.CharField(min_length=20, max_length=4000)


class AppealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appeal
        fields = ["id", "action", "status", "body", "decision_reasons", "decided_at", "created_at"]


class AppealDecisionSerializer(serializers.Serializer):
    upheld = serializers.BooleanField()
    reasons = serializers.CharField(min_length=20, max_length=4000)


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "action",
            "target_type",
            "target_id",
            "reason",
            "metadata",
            "created_at",
        ]
