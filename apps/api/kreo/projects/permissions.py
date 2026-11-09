"""Rôles d'un utilisateur sur un projet : owner (porteur), manager (co-orga), member."""

from kreo.common.permissions import (
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_MODERATOR,
    ROLE_OWNER,
    ROLE_TEAM_MEMBER,
    global_roles,
)

from .models import ProjectMember


def project_roles(user, project) -> set[str]:
    roles = global_roles(user)
    if user is None or not user.is_authenticated:
        return roles
    if project.owner_id == user.id:
        roles.add(ROLE_OWNER)
    membership = ProjectMember.objects.filter(project=project, user=user).first()
    if membership:
        roles.add(ROLE_TEAM_MEMBER if membership.role == "member" else membership.role)
    return roles


def is_project_manager(user, project) -> bool:
    """Porteur ou co-organisateur : peut modifier le projet, ses annonces et ses candidatures."""
    return bool({ROLE_OWNER, ROLE_MANAGER} & project_roles(user, project))


def can_view_project(user, project) -> bool:
    if project.is_public:
        return True
    roles = project_roles(user, project)
    return bool({ROLE_OWNER, ROLE_MANAGER, ROLE_TEAM_MEMBER, ROLE_MODERATOR, ROLE_ADMIN} & roles)
