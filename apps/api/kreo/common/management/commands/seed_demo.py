"""Jeu de données de démonstration pour l'environnement local (jamais en production)."""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from kreo.identity.models import BetaInvitation, User
from kreo.opportunities.services import create_opportunity, transition_opportunity
from kreo.profiles.services import ensure_profile
from kreo.projects.services import create_project, transition_project
from kreo.referentials.loaders import load_cities, load_disciplines
from kreo.referentials.models import City, Discipline

PASSWORD = "kreo-demo-2026"

PEOPLE = [
    ("camille@demo.kreo", "Camille Dubois", ["theatre", "mise-en-scene"], "1050", True),
    ("yanis@demo.kreo", "Yanis Benali", ["court-metrage", "montage"], "1080", True),
    ("lena@demo.kreo", "Léna Peeters", ["chant", "composition"], "1030", True),
    ("noa@demo.kreo", "Noa Vermeulen", ["danse", "performance"], "1060", False),
    ("sam@demo.kreo", "Sam Okafor", ["photographie", "graphisme"], "1000", False),
    ("ines@demo.kreo", "Inès Martin", ["theatre", "poesie-slam"], "1190", False),
]

PROJECTS = [
    (
        "camille@demo.kreo",
        "Pièce « La Nuit des Autres »",
        "Création théâtrale collective à Ixelles, sur la solitude urbaine. Six semaines de répétitions, trois représentations.",
        ["theatre"],
        "1050",
        False,
        [
            (
                "Casting comédien·ne·s",
                "On cherche deux comédien·ne·s et un·e régisseur·se lumière.",
                [
                    (
                        "Comédien·ne (rôle principal)",
                        "paid",
                        1,
                        "theatre",
                        {"playing_age_range": [25, 40], "languages": ["fr"]},
                        False,
                        "Cachet au forfait, détail en entretien.",
                    ),
                    (
                        "Comédien·ne (rôle secondaire)",
                        "expenses",
                        1,
                        "theatre",
                        {},
                        True,
                        "Défraiement transport et repas.",
                    ),
                    ("Régie lumière", "volunteer", 1, "lumiere", {}, True, ""),
                ],
            )
        ],
    ),
    (
        "yanis@demo.kreo",
        "Court-métrage « Lumière d'hiver »",
        "Fiction de 15 minutes tournée en janvier dans le quartier maritime. Équipe bienveillante, premier film pour plusieurs d'entre nous.",
        ["court-metrage"],
        "1080",
        False,
        [
            (
                "Équipe image et son",
                "Tournage sur 4 jours fin janvier.",
                [
                    (
                        "Chef·fe opérateur·rice",
                        "negotiable",
                        1,
                        "image-cadre",
                        {"experience_level": "confirmed"},
                        False,
                        "Selon budget obtenu.",
                    ),
                    ("Preneur·se de son", "expenses", 1, "sound-design", {}, True, ""),
                    ("Figurant·e·s", "volunteer", 6, None, {}, True, ""),
                ],
            )
        ],
    ),
    (
        "lena@demo.kreo",
        "Clip « Marée basse »",
        "Clip pour un titre pop-folk, tournage à la côte et à Bruxelles. Projet commercial financé par le label.",
        ["clip", "musique"],
        "1030",
        True,
        [
            (
                "Danseur·se·s pour le clip",
                "Chorégraphie contemporaine, deux jours de répétition.",
                [
                    (
                        "Danseur·se",
                        "paid",
                        2,
                        "danse",
                        {"dance_styles": ["contemporain"]},
                        False,
                        "150 € / jour.",
                    ),
                    ("Maquillage", "paid", 1, "maquillage-coiffure", {}, False, "Forfait journée."),
                ],
            )
        ],
    ),
]


class Command(BaseCommand):
    help = "Crée un jeu de démonstration : admin, membres, projets, annonces, invitations."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo ne s'exécute qu'en développement (DEBUG=true).")
        load_disciplines()
        load_cities()
        now = timezone.now()

        admin, _ = User.objects.get_or_create(
            email="admin@demo.kreo",
            defaults={
                "is_staff": True,
                "is_superuser": True,
                "is_moderator": True,
                "email_verified_at": now,
                "phone_verified_at": now,
            },
        )
        admin.set_password(PASSWORD)
        admin.save()
        ensure_profile(admin)

        users = {}
        for email, name, disciplines, postal, phone in PEOPLE:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "email_verified_at": now,
                    "phone_verified_at": now if phone else None,
                    "birth_date": "1994-05-12",
                    "terms_version": "2026-11",
                    "terms_accepted_at": now,
                },
            )
            if created:
                user.set_password(PASSWORD)
                user.save()
            profile = ensure_profile(user)
            profile.display_name = name
            profile.city = City.objects.get(postal_code=postal)
            profile.bio = f"{name} — {', '.join(disciplines)}. Basé·e à Bruxelles, ouvert·e aux collaborations."
            profile.experience_level = "intermediate"
            profile.onboarding_completed_at = now
            profile.save()
            profile.disciplines.set(Discipline.objects.filter(slug__in=disciplines))
            users[email] = user

        for (
            owner_email,
            title,
            description,
            disciplines,
            postal,
            commercial,
            opportunities,
        ) in PROJECTS:
            owner = users[owner_email]
            if owner.projects_owned.filter(title=title).exists():
                continue
            project = create_project(
                owner=owner,
                title=title,
                description=description,
                disciplines=list(Discipline.objects.filter(slug__in=disciplines)),
                city=City.objects.get(postal_code=postal),
                is_commercial=commercial,
                starts_on=(now + timedelta(days=30)).date(),
                ends_on=(now + timedelta(days=75)).date(),
            )
            for opp_title, opp_desc, roles in opportunities:
                opp = create_opportunity(
                    project=project,
                    actor=owner,
                    title=opp_title,
                    description=opp_desc,
                    has_intimate_scene=False,
                    roles=[
                        {
                            "title": r[0],
                            "compensation": r[1],
                            "slots": r[2],
                            "discipline": Discipline.objects.filter(slug=r[3]).first()
                            if r[3]
                            else None,
                            "requirements": r[4],
                            "beginner_friendly": r[5],
                            "compensation_details": r[6],
                            "deadline_at": now + timedelta(days=21),
                        }
                        for r in roles
                    ],
                )
                transition_opportunity(opportunity=opp, target="open", actor=owner)
            transition_project(project=project, target="active", actor=owner)

        codes = [BetaInvitation.objects.create(inviter=admin).code for _ in range(5)]
        self.stdout.write(self.style.SUCCESS("Jeu de démonstration prêt."))
        self.stdout.write(
            f"  Comptes : admin@demo.kreo et {', '.join(users)} — mot de passe : {PASSWORD}"
        )
        self.stdout.write(f"  Codes d'invitation : {', '.join(codes)}")
