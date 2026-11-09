"""
Catalogue des notifications (cahier des charges, section « Notifications : catalogue »).

Pour chaque clé : canaux par défaut, e-mail obligatoire (transactionnel, non désactivable),
mode e-mail (immediate | digest | if_unread_1h), sujet et gabarit.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class EventSpec:
    key: str
    in_app: bool
    email: bool
    push: bool
    mandatory_email: bool = False
    email_mode: str = "immediate"  # immediate | digest | if_unread_1h | none
    title_fr: str = ""
    ignore_quiet_hours: bool = False


CATALOG: dict[str, EventSpec] = {
    spec.key: spec
    for spec in [
        EventSpec(
            "application.new",
            True,
            True,
            True,
            email_mode="digest",
            title_fr="Nouvelle candidature sur un rôle",
        ),
        EventSpec("application.viewed", True, False, True, title_fr="Ta candidature a été vue"),
        EventSpec("application.shortlisted", True, False, True, title_fr="Tu es présélectionné·e"),
        EventSpec(
            "application.audition", True, False, True, title_fr="Tu es invité·e à une audition"
        ),
        EventSpec("application.offered", True, True, True, title_fr="Tu as reçu une offre"),
        EventSpec("application.accepted", True, True, True, title_fr="Offre acceptée"),
        EventSpec("application.declined", True, True, True, title_fr="Offre déclinée"),
        EventSpec("application.rejected", True, True, False, title_fr="Candidature non retenue"),
        EventSpec(
            "message.new",
            True,
            True,
            True,
            email_mode="if_unread_1h",
            title_fr="Nouveau message",
            ignore_quiet_hours=True,
        ),
        EventSpec("credit.proposed", True, True, True, title_fr="Un crédit t'est proposé"),
        EventSpec("credit.confirmed", True, True, False, title_fr="Crédit confirmé"),
        EventSpec("credit.disputed", True, True, False, title_fr="Crédit contesté"),
        EventSpec(
            "project.invitation",
            True,
            True,
            False,
            mandatory_email=True,
            title_fr="Invitation à co-organiser un projet",
        ),
        EventSpec(
            "applications.reminder_5d",
            True,
            True,
            False,
            title_fr="Des candidatures attendent une réponse depuis 5 jours",
        ),
        EventSpec(
            "opportunity.expiring_2d", True, True, False, title_fr="Ton annonce expire dans 2 jours"
        ),
        EventSpec(
            "saved_search.match", True, True, True, title_fr="Nouvelle annonce correspondante"
        ),
        EventSpec(
            "moderation.decision",
            True,
            True,
            False,
            mandatory_email=True,
            title_fr="Décision de modération",
            ignore_quiet_hours=True,
        ),
        EventSpec(
            "moderation.appeal_decided",
            True,
            True,
            False,
            mandatory_email=True,
            title_fr="Réponse à ton recours",
        ),
    ]
}


def spec_for(event_key: str) -> EventSpec:
    try:
        return CATALOG[event_key]
    except KeyError:
        raise ValueError(f"Événement de notification inconnu : {event_key}")
