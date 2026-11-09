# Schéma de référence

`kreo_schema.sql` est exporté depuis la base locale après `python manage.py migrate` (`pg_dump --schema-only`). Il sert de référence lisible ; **la source de vérité reste les migrations Django** (`apps/api/kreo/*/migrations`), rejouables à vide et vérifiées en CI.

Écarts assumés par rapport au schéma du cahier des charges V1.2 (section « Modèle de données complet ») :

- Les types `ENUM` PostgreSQL sont remplacés par des `varchar` + `choices` Django (évolution sans migration de type), les valeurs sont identiques.
- `users` reçoit des colonnes de sécurité et de consentement (`failed_login_count`, `locked_until`, `token_version`, `terms_version`, `terms_accepted_at`, `birth_date`, `phone_number`, `is_moderator`) ; `email` est un `varchar` avec index unique partiel sur `lower(email)` pour les comptes non supprimés (au lieu de `citext`).
- Tables techniques ajoutées : `one_time_tokens` (vérification e-mail, réinitialisation, code téléphone, hachés), `owner_response_stats` (délai médian de réponse recalculé chaque nuit), tables Django standard (`django_*`, `auth_*`).
- Recherche plein texte : configuration `kreo_french` (`french` + `unaccent`) et colonnes générées `search_vector` sur `projects` et `opportunities`, index GIN ; trigrammes sur `opportunities.title`.
- `applications.portfolio_media` est une table de liaison séparée des pièces jointes privées (`application_attachments`).

Régénérer : `PGPASSWORD=kreo pg_dump -h localhost -U kreo -d kreo --schema-only --no-owner --no-privileges > docs/schema/kreo_schema.sql`.
