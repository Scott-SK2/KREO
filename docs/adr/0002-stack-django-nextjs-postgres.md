# ADR 0002 — Stack : Django + DRF, Next.js, PostgreSQL 16, Redis + Celery

- **Statut** : accepté (hérité de la V1.0, précisé en V1.2)
- **Décision** :
  - **Backend** : Django 5.2 LTS + Django REST Framework, monolithe modulaire (`identity`, `profiles`, `projects`, `opportunities`, `applications`, `messaging`, `credits`, `notifications`, `moderation`, plus `referentials`, `media`, `social`, `common`).
  - **Base** : PostgreSQL 16 ; recherche plein texte via une configuration `kreo_french` (= `french` + `unaccent`), colonnes générées `tsvector` + index GIN, trigrammes `pg_trgm` sur les titres.
  - **Tâches** : Redis + Celery (e-mails, refus automatiques, rappels, délai médian, scan antivirus, redimensionnement).
  - **Web** : Next.js (App Router, TypeScript, Tailwind) ; rendu serveur des pages publiques pour le SEO et les aperçus Open Graph.
  - **Mobile (phase L)** : Expo / React Native, qui réutilise `api-client`, `ui-tokens`, `i18n`.
- **Pourquoi Django 5.2 plutôt que 6.x** : version LTS supportée jusqu'en 2028, écosystème (DRF, drf-spectacular, SimpleJWT) stable. Montée de version revue à chaque gate.
- **Hors périmètre** : WebSocket (polling 15 s suffit en bêta), Cloudinary (seulement si R2 + Pillow ne suffisent pas).
