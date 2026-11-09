from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import Q

from kreo.common.choices import CompensationType, OpportunityStatus, RoleStatus
from kreo.common.models import UUIDPrimaryKeyModel


class Opportunity(UUIDPrimaryKeyModel):
    """Annonce : appel publié pour un projet, avec un ou plusieurs rôles."""

    project = models.ForeignKey(
        "projects.Project", on_delete=models.CASCADE, related_name="opportunities"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+"
    )
    title = models.CharField(max_length=180)
    description = models.TextField()
    status = models.CharField(
        max_length=20, choices=OpportunityStatus.choices, default=OpportunityStatus.DRAFT
    )
    has_intimate_scene = models.BooleanField(default=False)
    moderated_at = models.DateTimeField(null=True, blank=True)
    template_discipline = models.ForeignKey(
        "referentials.Discipline",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
        help_text="Modèle d'annonce par discipline utilisé à la création.",
    )
    search_vector = models.GeneratedField(
        expression=SearchVector("title", weight="A", config="kreo_french")
        + SearchVector("description", weight="B", config="kreo_french"),
        output_field=SearchVectorField(),
        db_persist=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "opportunities"
        indexes = [
            models.Index(fields=["status", "-published_at"], name="idx_opps_status"),
            models.Index(fields=["project"], name="idx_opps_project"),
            GinIndex(fields=["search_vector"], name="idx_opps_fts"),
            GinIndex(name="idx_opps_title_trgm", fields=["title"], opclasses=["gin_trgm_ops"]),
        ]

    def __str__(self):
        return self.title

    @property
    def is_open(self):
        return self.status == OpportunityStatus.OPEN


class OpportunityRole(UUIDPrimaryKeyModel):
    """Rôle : poste recherché, avec sa rémunération, ses places et son échéance."""

    opportunity = models.ForeignKey(Opportunity, on_delete=models.CASCADE, related_name="roles")
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    discipline = models.ForeignKey(
        "referentials.Discipline",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="roles",
    )
    requirements = models.JSONField(default=dict, blank=True)  # clés de la liste fermée
    slots = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=RoleStatus.choices, default=RoleStatus.OPEN)
    compensation = models.CharField(max_length=20, choices=CompensationType.choices)
    compensation_details = models.TextField(blank=True, default="")
    city = models.ForeignKey(
        "referentials.City", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    deadline_at = models.DateTimeField(null=True, blank=True)
    beginner_friendly = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "opportunity_roles"
        ordering = ["created_at"]
        indexes = [
            models.Index(
                fields=["discipline", "status", "city", "compensation"], name="idx_roles_search"
            ),
            models.Index(
                fields=["deadline_at"], name="idx_roles_deadline", condition=Q(status="open")
            ),
        ]
        constraints = [models.CheckConstraint(condition=Q(slots__gt=0), name="role_slots_positive")]

    def __str__(self):
        return self.title

    @property
    def accepted_count(self) -> int:
        return self.applications.filter(status="accepted").count()

    @property
    def is_open(self) -> bool:
        return self.status == RoleStatus.OPEN and self.opportunity.status == OpportunityStatus.OPEN
