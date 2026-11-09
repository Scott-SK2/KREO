# KREO

**Une idée, des talents, un projet.**

KREO est une plateforme gratuite (web, puis iOS et Android) où les créateurs de toutes disciplines trouvent des projets, recrutent une équipe et gardent des crédits de collaboration confirmés. Elle démarre à Bruxelles, sans barrière de diplôme ni d'expérience. Produit indépendant développé par Genius Harmony.

Le cahier des charges de référence (V1.2) est dans [`docs/Cahier_des_charges_KREO_v1.2.pdf`](docs/Cahier_des_charges_KREO_v1.2.pdf). Le suivi des 38 fiches est dans [`docs/backlog.md`](docs/backlog.md), les décisions d'architecture dans [`docs/adr/`](docs/adr/).

## Organisation du dépôt

```
apps/
  api/        API REST Django + DRF (monolithe modulaire, PostgreSQL 16, Redis + Celery)
  web/        Web Next.js (TypeScript, Tailwind, next-intl)
  mobile/     Expo / React Native — phase L (lancement public)
packages/
  api-client/ Client TypeScript généré depuis le contrat OpenAPI de l'API
  ui-tokens/  Design tokens KREO (couleurs, typographies, espacements) + variables CSS
  i18n/       Clés de traduction partagées web + mobile (FR en V1, NL puis EN)
docs/         Cahier des charges, ADR, backlog
infra/        Déploiement (à compléter en sprint 0, voir ADR 0005)
```

## Démarrer

Prérequis : Node 22 + pnpm 10, Python 3.12+, Docker (ou PostgreSQL 16 et Redis locaux).

```bash
pnpm install
docker compose up -d                     # PostgreSQL 16, Redis, Mailpit (e-mails locaux sur :8025)
```

API :

```bash
cd apps/api
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python manage.py migrate
python manage.py load_referentials       # disciplines + 19 communes bruxelloises (FR/NL/EN)
python manage.py seed_demo               # comptes et projets de démonstration
python manage.py runserver               # http://localhost:8000/api/docs/
```

Web :

```bash
cp apps/web/.env.example apps/web/.env.local
pnpm --filter @kreo/web dev              # http://localhost:3000
```

Client API : après toute modification de l'API, régénérer le contrat et les types :

```bash
cd apps/api && python manage.py spectacular --format openapi-json --file ../../packages/api-client/openapi.json
pnpm api:openapi
```

## Qualité et CI

`pnpm lint`, `pnpm typecheck`, `pnpm test`, `pnpm build` côté JavaScript ; `ruff`, `pytest`, `makemigrations --check` et validation du schéma OpenAPI côté API. Le workflow GitHub Actions (`.github/workflows/ci.yml`) exécute tout cela sur chaque pull request et déploie en staging à chaque fusion sur `main` (hook à brancher, ADR 0005).

Définition de terminé (cahier des charges) : code revu, migrations rejouables, contrôle d'accès testé (autorisé et refusé), tests unitaires et API verts, E2E du parcours concerné vert, accessibilité vérifiée, journaux sans données personnelles, documentation OpenAPI à jour, retour arrière possible.

## Règles clés du produit

- Inscription sur code d'invitation pendant la bêta (5 invitations par membre), comptes 18+.
- Toute transition de statut passe par un service métier transactionnel et un endpoint `/transition` ; une transition absente des tables du cahier des charges renvoie 409.
- Chaque rôle d'une annonce a sa rémunération ; « bénévole » est refusé sur un projet commercial ; critères de casting limités à une liste fermée.
- À la clôture d'une annonce, toute candidature encore ouverte reçoit un refus courtois automatique, une seule fois.
- Les crédits n'apparaissent que confirmés par les deux parties. Jamais de classement payant.
