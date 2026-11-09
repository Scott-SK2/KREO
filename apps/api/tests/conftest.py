import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from kreo.identity.models import BetaInvitation, User
from kreo.profiles.services import ensure_profile
from kreo.referentials.loaders import load_cities, load_disciplines
from kreo.referentials.models import City, Discipline


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        load_disciplines()
        load_cities()


@pytest.fixture
def api():
    return APIClient()


def make_user(
    email, *, phone=False, verified=True, staff=False, moderator=False, display_name=None
):
    user = User.objects.create_user(
        email=email,
        password="MotDePasse-Solide-42",
        email_verified_at=timezone.now() if verified else None,
        phone_verified_at=timezone.now() if phone else None,
        is_staff=staff,
        is_moderator=moderator,
    )
    profile = ensure_profile(user)
    if display_name:
        profile.display_name = display_name
        profile.save()
    return user


@pytest.fixture
def owner(db):
    return make_user("porteur@example.com", phone=True, display_name="Camille Porteur")


@pytest.fixture
def coorga(db):
    return make_user("coorga@example.com", phone=True, display_name="Sam Co-orga")


@pytest.fixture
def candidate(db):
    return make_user("candidat@example.com", display_name="Alex Candidat")


@pytest.fixture
def other(db):
    return make_user("autre@example.com", display_name="Noa Autre")


@pytest.fixture
def moderator(db):
    return make_user("modo@example.com", moderator=True, display_name="Modo")


@pytest.fixture
def admin(db):
    return make_user("admin@example.com", staff=True, display_name="Admin")


@pytest.fixture
def invitation(db, owner):
    return BetaInvitation.objects.create(inviter=owner)


@pytest.fixture
def disciplines(db):
    return list(Discipline.objects.filter(slug__in=["theatre", "danse", "court-metrage"]))


@pytest.fixture
def brussels(db):
    return City.objects.get(postal_code="1000")


def as_user(api, user):
    api.force_authenticate(user=user)
    return api


@pytest.fixture
def project(db, owner, disciplines, brussels):
    from kreo.projects.services import create_project

    return create_project(
        owner=owner,
        title="Court-métrage « Lumière d'hiver »",
        description="Un court-métrage tourné à Bruxelles en janvier, équipe bienveillante.",
        disciplines=disciplines,
        city=brussels,
    )


@pytest.fixture
def open_opportunity(db, project, owner, brussels):
    from kreo.opportunities.services import create_opportunity, transition_opportunity

    opp = create_opportunity(
        project=project,
        actor=owner,
        title="Casting théâtre : deux rôles",
        description="On cherche un·e comédien·ne principal·e (payé) et un·e assistant·e (bénévole).",
        has_intimate_scene=False,
        roles=[
            {
                "title": "Comédien·ne principal·e",
                "compensation": "paid",
                "slots": 1,
                "discipline": Discipline.objects.get(slug="theatre"),
                "city": brussels,
            },
            {
                "title": "Assistant·e plateau",
                "compensation": "volunteer",
                "slots": 2,
                "beginner_friendly": True,
            },
        ],
    )
    return transition_opportunity(opportunity=opp, target="open", actor=owner)
