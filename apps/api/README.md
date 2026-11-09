# KREO — API (Django + DRF)

Monolithe modulaire : `identity`, `referentials`, `media`, `profiles`, `projects`, `opportunities`, `applications`, `messaging`, `credits`, `notifications`, `moderation`, `social` (V1.1), `common`.

## Démarrer en local

```bash
cd apps/api
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # jamais de vraie clé dans le dépôt
docker compose -f ../../docker-compose.yml up -d   # PostgreSQL 16 + Redis + Mailpit
python manage.py migrate
python manage.py load_referentials   # 53 disciplines, 19 communes FR/NL/EN
python manage.py seed_demo           # comptes et projets de démonstration (dev uniquement)
python manage.py runserver
```

- Documentation interactive : http://localhost:8000/api/docs/ — schéma : http://localhost:8000/api/schema/
- Admin Django : http://localhost:8000/admin/ (`admin@demo.kreo` / `kreo-demo-2026` après `seed_demo`)
- E-mails locaux : http://localhost:8025 (Mailpit)

## Qualité

```bash
ruff check . && ruff format --check .
pytest -q
python manage.py makemigrations --check --dry-run
python manage.py spectacular --format openapi-json --file openapi.json --validate
```

## Conventions

- Toute transition de statut passe par `POST …/{id}/transition` ; une transition absente des tables du cahier des charges renvoie 409.
- Erreurs au format `application/problem+json` avec un `type` stable (`https://kreo.be/problems/<slug>`).
- Aucune donnée personnelle dans les journaux (formatteur JSON avec masquage e-mail/téléphone).
- Les règles d'accès sont vérifiées côté API, objet par objet (`kreo/projects/permissions.py`, services de chaque module).
