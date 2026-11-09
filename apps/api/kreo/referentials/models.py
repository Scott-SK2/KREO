from django.db import models


class Discipline(models.Model):
    """Taxonomie des disciplines, administrable sans migration, libellés FR/NL/EN."""

    slug = models.SlugField(max_length=80, unique=True)
    label_i18n = models.JSONField()
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.PROTECT, related_name="children"
    )
    active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        db_table = "disciplines"
        ordering = ["sort_order", "slug"]

    def __str__(self):
        return self.slug

    def label(self, locale="fr"):
        return self.label_i18n.get(locale) or self.label_i18n.get("fr", self.slug)


class City(models.Model):
    """Communes de référence (Bruxelles d'abord), libellés FR/NL/EN."""

    country_code = models.CharField(max_length=2, default="BE")
    postal_code = models.CharField(max_length=10, blank=True, default="")
    label_i18n = models.JSONField()
    lat = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    lng = models.DecimalField(max_digits=8, decimal_places=5, null=True, blank=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "cities"
        ordering = ["postal_code"]
        verbose_name_plural = "cities"

    def __str__(self):
        return self.label_i18n.get("fr", str(self.pk))

    def label(self, locale="fr"):
        return self.label_i18n.get(locale) or self.label_i18n.get("fr", "")
