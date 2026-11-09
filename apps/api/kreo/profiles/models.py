from django.conf import settings
from django.db import models

from kreo.common.choices import ExperienceLevel, Visibility


class ArtistProfile(models.Model):
    """Profil public d'un membre. Aucun contact personnel affiché."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE, related_name="profile"
    )
    slug = models.SlugField(max_length=80, unique=True)
    display_name = models.CharField(max_length=120)
    bio = models.TextField(blank=True, default="")
    city = models.ForeignKey(
        "referentials.City",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="profiles",
    )
    avatar = models.ForeignKey(
        "media.MediaAsset", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PUBLIC
    )
    experience_level = models.CharField(
        max_length=30, choices=ExperienceLevel.choices, blank=True, default=""
    )
    video_links = models.JSONField(default=list, blank=True)  # YouTube / Vimeo uniquement
    external_links = models.JSONField(default=list, blank=True)
    open_to_beginner_roles = models.BooleanField(default=True)
    onboarding_completed_at = models.DateTimeField(null=True, blank=True)
    disciplines = models.ManyToManyField(
        "referentials.Discipline", through="ProfileDiscipline", related_name="profiles"
    )
    media = models.ManyToManyField("media.MediaAsset", through="ProfileMedia", related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "artist_profiles"
        indexes = [
            models.Index(fields=["visibility"], name="idx_profiles_visibility"),
        ]

    def __str__(self):
        return self.slug

    @property
    def completion(self) -> dict:
        """Indicateur de complétion progressive (0-100)."""
        checks = {
            "display_name": bool(self.display_name),
            "disciplines": self.disciplines.exists(),
            "city": self.city_id is not None,
            "bio": len(self.bio or "") >= 60,
            "avatar": self.avatar_id is not None,
            "gallery": self.media.exists(),
            "links": bool(self.video_links or self.external_links),
            "level": bool(self.experience_level),
        }
        score = round(100 * sum(checks.values()) / len(checks))
        return {"score": score, "missing": [k for k, ok in checks.items() if not ok]}


class ProfileDiscipline(models.Model):
    profile = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, db_column="user_id")
    discipline = models.ForeignKey("referentials.Discipline", on_delete=models.PROTECT)

    class Meta:
        db_table = "profile_disciplines"
        constraints = [
            models.UniqueConstraint(fields=["profile", "discipline"], name="uq_profile_discipline")
        ]


class ProfileAttribute(models.Model):
    """Attributs de casting : clés limitées à la liste fermée, privés par défaut."""

    profile = models.ForeignKey(
        ArtistProfile, on_delete=models.CASCADE, db_column="user_id", related_name="attributes"
    )
    attribute_key = models.CharField(max_length=80)
    value_json = models.JSONField()
    visibility = models.CharField(
        max_length=12, choices=Visibility.choices, default=Visibility.PRIVATE
    )

    class Meta:
        db_table = "profile_attributes"
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "attribute_key"], name="uq_profile_attribute"
            )
        ]


class ProfileMedia(models.Model):
    profile = models.ForeignKey(ArtistProfile, on_delete=models.CASCADE, db_column="user_id")
    media = models.ForeignKey("media.MediaAsset", on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=0)

    class Meta:
        db_table = "profile_media"
        ordering = ["sort_order"]
        constraints = [
            models.UniqueConstraint(fields=["profile", "media"], name="uq_profile_media")
        ]
