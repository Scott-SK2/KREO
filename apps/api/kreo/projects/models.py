from django.conf import settings
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector, SearchVectorField
from django.db import models
from django.db.models import F, Q

from kreo.common.choices import ProjectMemberRole, ProjectStatus, Visibility
from kreo.common.models import UUIDPrimaryKeyModel

PUBLIC_PROJECT_STATUSES = (
    ProjectStatus.PREPARING,
    ProjectStatus.ACTIVE,
    ProjectStatus.COMPLETED,
    ProjectStatus.CANCELLED,
    ProjectStatus.ARCHIVED,
)


class Project(UUIDPrimaryKeyModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="projects_owned"
    )
    slug = models.SlugField(max_length=120, unique=True)
    title = models.CharField(max_length=180)
    description = models.TextField()
    city = models.ForeignKey(
        "referentials.City",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="projects",
    )
    starts_on = models.DateField(null=True, blank=True)
    ends_on = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=ProjectStatus.choices, default=ProjectStatus.DRAFT
    )
    is_commercial = models.BooleanField(default=False)
    cover = models.ForeignKey(
        "media.MediaAsset", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    disciplines = models.ManyToManyField(
        "referentials.Discipline", through="ProjectDiscipline", related_name="projects"
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="ProjectMember", related_name="projects_joined"
    )
    search_vector = models.GeneratedField(
        expression=SearchVector("title", weight="A", config="kreo_french")
        + SearchVector("description", weight="B", config="kreo_french"),
        output_field=SearchVectorField(),
        db_persist=True,
    )
    published_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "projects"
        indexes = [
            models.Index(fields=["status", "city", "-created_at"], name="idx_projects_status_city"),
            GinIndex(fields=["search_vector"], name="idx_projects_fts"),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(ends_on__isnull=True)
                | Q(starts_on__isnull=True)
                | Q(ends_on__gte=F("starts_on")),
                name="project_dates_order",
            )
        ]

    def __str__(self):
        return self.title

    @property
    def is_public(self):
        return self.status in PUBLIC_PROJECT_STATUSES and self.visibility == Visibility.PUBLIC


class ProjectDiscipline(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    discipline = models.ForeignKey("referentials.Discipline", on_delete=models.PROTECT)

    class Meta:
        db_table = "project_disciplines"
        constraints = [
            models.UniqueConstraint(fields=["project", "discipline"], name="uq_project_discipline")
        ]


class ProjectMember(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships"
    )
    role = models.CharField(max_length=30, choices=ProjectMemberRole.choices)
    role_title = models.CharField(max_length=150, blank=True, default="")
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_members"
        constraints = [
            models.UniqueConstraint(fields=["project", "user"], name="uq_project_member")
        ]


class ProjectInvitation(UUIDPrimaryKeyModel):
    """Invitation de co-organisateur ou membre, par e-mail ou lien, valable 7 jours."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="invitations")
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    email = models.EmailField(blank=True, default="")
    role = models.CharField(
        max_length=30,
        choices=[(ProjectMemberRole.MANAGER, "manager"), (ProjectMemberRole.MEMBER, "member")],
    )
    token_hash = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    accepted_at = models.DateTimeField(null=True, blank=True)
    accepted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "project_invitations"


class ProjectUpdate(UUIDPrimaryKeyModel):
    """Actualité de projet : texte + jusqu'à 4 photos sur la page du projet."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="updates")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+")
    body = models.TextField()
    media = models.ManyToManyField(
        "media.MediaAsset", through="ProjectUpdateMedia", related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "project_updates"
        ordering = ["-created_at"]


class ProjectUpdateMedia(models.Model):
    update = models.ForeignKey(ProjectUpdate, on_delete=models.CASCADE)
    media = models.ForeignKey("media.MediaAsset", on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "project_update_media"
        ordering = ["sort_order"]
        constraints = [models.UniqueConstraint(fields=["update", "media"], name="uq_update_media")]
