# ADR 0003 — Une seule source de types : OpenAPI 3.1 généré depuis DRF

- **Statut** : accepté
- **Décision** : `drf-spectacular` génère `openapi.json` (`python manage.py spectacular`). `packages/api-client` exécute `openapi-typescript` pour produire `src/schema.d.ts`, et expose un client `openapi-fetch` typé. Web et mobile consomment ce client.
- **Règles d'API** (cahier des charges) : REST JSON sous `/api/v1`, identifiants UUID, dates ISO 8601 UTC, pagination par curseur, erreurs `application/problem+json` (RFC 9457) avec un `type` stable (ex. `https://kreo.be/problems/invitation-invalid`) que le front traduit via les clés `errors.*` de `@kreo/i18n`.
- **Transitions** : toute transition de statut passe par `POST .../{id}/transition` avec le statut cible ; jamais de PATCH direct du champ. Une transition absente des tables du cahier des charges renvoie **409**.
- **CI** : le schéma est régénéré et validé à chaque PR ; une divergence entre `openapi.json` committé et le schéma généré fait échouer la fusion.
