"""Énumérations partagées, alignées sur les types ENUM du schéma de référence."""

from django.db import models


class AccountStatus(models.TextChoices):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class ProjectStatus(models.TextChoices):
    DRAFT = "draft"
    PREPARING = "preparing"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ARCHIVED = "archived"


class OpportunityStatus(models.TextChoices):
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class RoleStatus(models.TextChoices):
    OPEN = "open"
    FILLED = "filled"
    CLOSED = "closed"


class CompensationType(models.TextChoices):
    PAID = "paid"
    VOLUNTEER = "volunteer"
    EXPENSES = "expenses"
    NEGOTIABLE = "negotiable"


class ApplicationStatus(models.TextChoices):
    SUBMITTED = "submitted"
    VIEWED = "viewed"
    SHORTLISTED = "shortlisted"
    AUDITION = "audition"
    OFFERED = "offered"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


APPLICATION_OPEN_STATUSES = (
    ApplicationStatus.SUBMITTED,
    ApplicationStatus.VIEWED,
    ApplicationStatus.SHORTLISTED,
    ApplicationStatus.AUDITION,
    ApplicationStatus.OFFERED,
)


class CreditStatus(models.TextChoices):
    PROPOSED = "proposed"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
    DECLINED = "declined"


class Visibility(models.TextChoices):
    PUBLIC = "public"
    FOLLOWERS = "followers"
    PRIVATE = "private"


class ProjectMemberRole(models.TextChoices):
    OWNER = "owner"
    MANAGER = "manager"  # co-organisateur
    MEMBER = "member"


class ExperienceLevel(models.TextChoices):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    CONFIRMED = "confirmed"
    PROFESSIONAL = "professional"


class ReportTargetType(models.TextChoices):
    USER = "user"
    PROJECT = "project"
    OPPORTUNITY = "opportunity"
    PROJECT_UPDATE = "project_update"
    MESSAGE = "message"
    POST = "post"
    COMMENT = "comment"


class ReportStatus(models.TextChoices):
    OPEN = "open"
    IN_REVIEW = "in_review"
    ACTIONED = "actioned"
    DISMISSED = "dismissed"


class ReportPriority(models.IntegerChoices):
    PERSON_SAFETY = 1, "Sécurité des personnes (24 h)"
    STANDARD = 2, "Standard (48 h)"
    LOW = 3, "Faible"


class AppealStatus(models.TextChoices):
    OPEN = "open"
    UPHELD = "upheld"
    REVERSED = "reversed"


class FavoriteTargetType(models.TextChoices):
    OPPORTUNITY = "opportunity"
    PROJECT = "project"
    PROFILE = "profile"


class DevicePlatform(models.TextChoices):
    IOS = "ios"
    ANDROID = "android"


# Liste fermée des attributs de casting (RGPD : aucune donnée de l'article 9).
CASTING_ATTRIBUTE_KEYS = {
    "playing_age_range": {"type": "range", "min": 18, "max": 99},
    "languages": {
        "type": "list",
        "values": ["fr", "nl", "en", "de", "es", "it", "pt", "ar", "other"],
    },
    "skills": {"type": "list", "max_items": 20},
    "voice_type": {
        "type": "enum",
        "values": ["soprano", "mezzo", "alto", "tenor", "baritone", "bass", "other"],
    },
    "instruments": {"type": "list", "max_items": 10},
    "dance_styles": {"type": "list", "max_items": 10},
    "costume_sizes": {"type": "object"},  # seules mensurations autorisées : tailles de costume
    "driving_licence": {"type": "bool"},
    "union_member": {"type": "bool"},
}
