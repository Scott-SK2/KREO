"""Chargement idempotent des référentiels depuis les fichiers JSON du dépôt."""

import json
from pathlib import Path

from django.db import transaction

from .models import City, Discipline

DATA_DIR = Path(__file__).resolve().parent / "data"


@transaction.atomic
def load_disciplines() -> int:
    data = json.loads((DATA_DIR / "disciplines.json").read_text(encoding="utf-8"))
    count = 0
    for order, parent in enumerate(data):
        parent_obj, _ = Discipline.objects.update_or_create(
            slug=parent["slug"],
            defaults={"label_i18n": parent["label"], "parent": None, "sort_order": order},
        )
        count += 1
        for child_order, child in enumerate(parent.get("children", [])):
            Discipline.objects.update_or_create(
                slug=child["slug"],
                defaults={
                    "label_i18n": child["label"],
                    "parent": parent_obj,
                    "sort_order": child_order,
                },
            )
            count += 1
    return count


@transaction.atomic
def load_cities() -> int:
    data = json.loads((DATA_DIR / "cities_brussels.json").read_text(encoding="utf-8"))
    count = 0
    for row in data:
        City.objects.update_or_create(
            country_code="BE",
            postal_code=row["postal_code"],
            defaults={"label_i18n": row["label"], "lat": row["lat"], "lng": row["lng"]},
        )
        count += 1
    return count
