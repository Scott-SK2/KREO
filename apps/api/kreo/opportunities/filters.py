"""Recherche d'annonces : texte libre (french + unaccent + trigrammes), filtres combinables."""

from django.contrib.postgres.search import SearchQuery, SearchRank, TrigramSimilarity
from django.db.models import Q
from django.utils import timezone

from kreo.common.choices import OpportunityStatus, RoleStatus, Visibility
from kreo.moderation.services import blocked_user_ids

from .models import Opportunity


def search_opportunities(params, user):
    qs = (
        Opportunity.objects.filter(
            status=OpportunityStatus.OPEN,
            project__visibility=Visibility.PUBLIC,
            project__owner__status="active",
        )
        .select_related("project__owner__profile", "project__city", "project__cover")
        .prefetch_related("project__disciplines", "roles__discipline", "roles__city")
    )
    if user is not None and user.is_authenticated:
        blocked = blocked_user_ids(user)
        if blocked:
            qs = qs.exclude(project__owner_id__in=blocked)

    role_filter = Q(roles__status=RoleStatus.OPEN)
    if params.get("discipline"):
        slugs = [s for s in params["discipline"].split(",") if s]
        role_filter &= Q(roles__discipline__slug__in=slugs) | Q(
            roles__discipline__parent__slug__in=slugs
        )
    if params.get("city"):
        ids = [c for c in params["city"].split(",") if c.isdigit()]
        role_filter &= Q(roles__city_id__in=ids) | (
            Q(roles__city__isnull=True) & Q(project__city_id__in=ids)
        )
    if params.get("compensation"):
        role_filter &= Q(roles__compensation__in=params["compensation"].split(","))
    if params.get("beginner_friendly") == "true":
        role_filter &= Q(roles__beginner_friendly=True)
    if params.get("deadline_after"):
        role_filter &= Q(roles__deadline_at__gte=params["deadline_after"]) | Q(
            roles__deadline_at__isnull=True
        )
    if params.get("deadline_before"):
        role_filter &= Q(roles__deadline_at__lte=params["deadline_before"])
    if params.get("level"):
        role_filter &= Q(roles__requirements__experience_level=params["level"])
    qs = qs.filter(role_filter)

    if params.get("starts_after"):
        qs = qs.filter(
            Q(project__starts_on__gte=params["starts_after"]) | Q(project__starts_on__isnull=True)
        )
    if params.get("project_discipline"):
        qs = qs.filter(project__disciplines__slug=params["project_discipline"])

    q = (params.get("q") or "").strip()
    sort = params.get("sort", "recent")
    if q:
        query = SearchQuery(q, config="kreo_french", search_type="websearch")
        qs = qs.annotate(
            rank=SearchRank("search_vector", query),
            similarity=TrigramSimilarity("title", q),
        ).filter(Q(search_vector=query) | Q(similarity__gt=0.3))
        if sort == "relevance":
            return qs.distinct().order_by("-rank", "-similarity", "-published_at", "-id")
    return qs.distinct().order_by("-published_at", "-id")


def default_deadline_filter():
    return timezone.now()
