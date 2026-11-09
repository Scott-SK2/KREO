"""Export RGPD : toutes les données d'un membre, en JSON."""

from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict


def _rows(qs, exclude=()):
    return [
        {k: v for k, v in model_to_dict(obj).items() if k not in exclude} | {"id": str(obj.pk)}
        for obj in qs
    ]


def build_account_export(user) -> dict:
    from kreo.applications.models import Application, Favorite, SavedSearch
    from kreo.credits.models import ProjectCredit
    from kreo.messaging.models import Message
    from kreo.notifications.models import Notification, NotificationPreference
    from kreo.profiles.models import ArtistProfile, ProfileAttribute
    from kreo.projects.models import Project, ProjectMember, ProjectUpdate

    profile = ArtistProfile.objects.filter(user=user).first()
    data = {
        "account": {
            "id": str(user.id),
            "email": user.email,
            "locale": user.locale,
            "status": user.status,
            "created_at": user.created_at,
            "email_verified_at": user.email_verified_at,
            "phone_verified_at": user.phone_verified_at,
            "terms_version": user.terms_version,
            "terms_accepted_at": user.terms_accepted_at,
        },
        "profile": model_to_dict(profile, exclude=["avatar"]) if profile else None,
        "profile_attributes": _rows(ProfileAttribute.objects.filter(profile_id=user.id)),
        "projects_owned": _rows(Project.objects.filter(owner=user), exclude=("cover",)),
        "project_memberships": _rows(ProjectMember.objects.filter(user=user)),
        "project_updates": _rows(ProjectUpdate.objects.filter(author=user)),
        "applications": _rows(Application.objects.filter(applicant=user)),
        "messages": _rows(Message.objects.filter(sender=user)),
        "credits": _rows(ProjectCredit.objects.filter(user=user)),
        "favorites": _rows(Favorite.objects.filter(user=user)),
        "saved_searches": _rows(SavedSearch.objects.filter(user=user)),
        "notifications": _rows(Notification.objects.filter(recipient=user)),
        "notification_preferences": _rows(NotificationPreference.objects.filter(user=user)),
    }
    # Normalisation JSON (UUID, dates) via l'encodeur Django.
    import json

    return json.loads(json.dumps(data, cls=DjangoJSONEncoder))
