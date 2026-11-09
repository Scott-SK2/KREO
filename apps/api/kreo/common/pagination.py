from rest_framework.pagination import CursorPagination


class CreatedAtCursorPagination(CursorPagination):
    """Pagination par curseur, du plus récent au plus ancien."""

    page_size = 20
    max_page_size = 50
    page_size_query_param = "page_size"
    ordering = "-created_at"
    cursor_query_param = "cursor"


class SubmittedAtCursorPagination(CreatedAtCursorPagination):
    ordering = "-submitted_at"


class PublishedAtCursorPagination(CreatedAtCursorPagination):
    ordering = ("-published_at", "-id")


class OldestFirstCursorPagination(CreatedAtCursorPagination):
    ordering = "created_at"


class ModerationQueuePagination(CreatedAtCursorPagination):
    """Sécurité des personnes d'abord (priorité 1), puis les plus anciens."""

    ordering = ("priority", "created_at")
