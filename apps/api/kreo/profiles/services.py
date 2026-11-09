from django.db import transaction

from kreo.common.utils import unique_slug

from .models import ArtistProfile, ProfileMedia


def ensure_profile(user) -> ArtistProfile:
    """Crée le profil à la première visite du tableau de bord (onboarding)."""
    profile = ArtistProfile.objects.filter(user=user).first()
    if profile:
        return profile
    base = user.email.split("@")[0]
    return ArtistProfile.objects.create(
        user=user, slug=unique_slug(ArtistProfile, base), display_name=base[:120]
    )


@transaction.atomic
def set_gallery(profile: ArtistProfile, media_ids: list) -> None:
    from kreo.media.models import MediaAsset

    assets = {
        str(a.id): a
        for a in MediaAsset.objects.filter(
            id__in=media_ids, owner=profile.user, mime_type__startswith="image/"
        )
    }
    ProfileMedia.objects.filter(profile=profile).delete()
    ProfileMedia.objects.bulk_create(
        [
            ProfileMedia(profile=profile, media=assets[str(mid)], sort_order=i)
            for i, mid in enumerate(media_ids)
            if str(mid) in assets
        ]
    )
