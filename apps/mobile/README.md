# KREO mobile (phase L)

Application Expo / React Native prévue pour le lancement public (fiches 30 à 33, 37, 38). Elle réutilisera `@kreo/api-client`, `@kreo/ui-tokens` et `@kreo/i18n`.

L'API est déjà prête pour le mobile : envoyer l'en-tête `X-Client: mobile` sur `/auth/login`, `/auth/verify-email` et `/auth/refresh` pour recevoir les jetons dans le corps de la réponse (à stocker dans le stockage sécurisé de l'appareil), puis `Authorization: Bearer <access>`. `POST /devices` enregistre le jeton push une fois `FEATURE_PUSH` activé.
