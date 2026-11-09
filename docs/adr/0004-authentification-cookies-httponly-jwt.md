# ADR 0004 — Authentification : JWT courts, cookies HttpOnly sur le web, Bearer sur mobile

- **Statut** : accepté
- **Décision** :
  - Mots de passe hachés **Argon2**. Jetons d'accès 15 min, refresh 30 jours **rotatifs**.
  - **Web** : les deux jetons sont posés en cookies `HttpOnly; Secure; SameSite=Lax` (`kreo_access` sur `/`, `kreo_refresh` sur `/api/v1/auth`). Le JavaScript ne voit jamais les jetons.
  - **Mobile** : en-tête `X-Client: mobile` → les jetons sont renvoyés dans le corps et stockés dans le stockage sécurisé de l'appareil.
  - **Déconnexion de tous les appareils** : chaque jeton porte un claim `tv` (version) comparé à `users.token_version` ; incrémenter la version révoque tout.
  - Verrouillage 15 min après 5 échecs de connexion ; vérification d'e-mail obligatoire (lien 24 h) ; téléphone confirmé avant la première annonce (porteur vérifié, numéro jamais affiché).
- **Colonnes ajoutées au schéma de référence** (documentées ici, appliquées par les migrations Django) : `users.failed_login_count`, `locked_until`, `token_version`, `terms_version`, `terms_accepted_at`, `birth_date`, `phone_number`, `is_moderator` ; table `one_time_tokens` (vérification e-mail, réinitialisation, code téléphone, tous hachés).
