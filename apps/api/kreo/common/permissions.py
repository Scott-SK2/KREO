from rest_framework.permissions import SAFE_METHODS, BasePermission

ROLE_VISITOR = "visitor"
ROLE_MEMBER = "member"
ROLE_OWNER = "owner"  # porteur
ROLE_MANAGER = "manager"  # co-organisateur
ROLE_TEAM_MEMBER = "team_member"  # membre de l'équipe d'un projet
ROLE_MODERATOR = "moderator"
ROLE_ADMIN = "admin"


def global_roles(user) -> set[str]:
    """Rôles globaux d'un utilisateur (hors contexte projet)."""
    if user is None or not user.is_authenticated:
        return {ROLE_VISITOR}
    roles = {ROLE_MEMBER}
    if getattr(user, "is_moderator", False):
        roles.add(ROLE_MODERATOR)
    if user.is_staff:
        roles.update({ROLE_MODERATOR, ROLE_ADMIN})
    return roles


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(
            request.user and request.user.is_authenticated
        )


class IsModerator(BasePermission):
    message = "Réservé à l'équipe de modération."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated) and (
            request.user.is_moderator or request.user.is_staff
        )


class IsAdmin(BasePermission):
    message = "Réservé aux administrateurs."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class IsActiveAccount(BasePermission):
    """Un compte suspendu peut lire mais ne peut rien publier ni envoyer."""

    message = "Ton compte est suspendu. Consulte la motivation reçue par e-mail."

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return bool(user and user.is_authenticated and user.status == "active")
