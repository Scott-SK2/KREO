# Backlog KREO — suivi des 38 fiches

Source : cahier des charges V1.2 (`docs/Cahier_des_charges_KREO_v1.2.pdf`). Les critères d'acceptation complets y figurent.
État : ✅ livré · 🟡 partiel · ⬜ à faire. « Livré » = code + tests ; la recette en staging par le product owner reste à faire.

## Phase B — bêta web (104 j)

| #   | Fiche                                               | Prio | Sprint | État            | Notes                                                                                      |
| --- | --------------------------------------------------- | ---- | ------ | --------------- | ------------------------------------------------------------------------------------------ |
| 1   | Monorepo, CI, déploiement staging                   | P0   | B1     | 🟡              | Monorepo, CI lint+tests+build OK ; hook de déploiement staging à brancher (ADR 0005)       |
| 2   | Environnements, secrets, journaux, Sentry           | P0   | B1     | ✅              | `.env.example`, settings dev/test/prod, journaux JSON sans PII, Sentry sans PII            |
| 3   | Schéma, migrations, taxonomie et communes           | P0   | B1     | ✅              | 40 tables + tables techniques, migrations rejouables, 53 disciplines, 19 communes FR/NL/EN |
| 4   | Design system web                                   | P0   | B1     | 🟡              | Tokens + composants de base ; contraste AA testé ; à étendre (modale, toasts, onglets)     |
| 5   | Inscription sur invitation, vérification, connexion | P0   | B1     | ✅              | Code invalide/expiré refusé, lien 24 h, verrouillage après 5 échecs                        |
| 6   | Onboarding multidiscipline                          | P0   | B2     | ✅ API / 🟡 web | 2 disciplines minimum, sans photo                                                          |
| 7   | Profil public, confidentialité, galerie             | P0   | B2     | ✅ API / ⬜ web | Attributs de casting privés par défaut, liste fermée                                       |
| 8   | Pipeline médias                                     | P0   | B2     | 🟡              | MIME par signature, 10 Mo, 3 tailles WebP, URL signée 5 min ; scanner antivirus à brancher |
| 9   | Projets : création, statuts, propriété              | P0   | B2     | ✅ API / ⬜ web | Transitions invalides → 409                                                                |
| 10  | Équipe et co-organisateurs                          | P0   | B2     | ✅ API / ⬜ web | Invitation lien ou e-mail 7 jours, retrait immédiat                                        |
| 11  | Actualités de projet                                | P1   | B2     | ✅ API / ⬜ web | Texte + 4 photos, signalables                                                              |
| 12  | Annonces et rôles                                   | P0   | B3     | ✅ API / ⬜ web | Rémunération par rôle, fermeture auto quand pourvu                                         |
| 13  | Règles de publication, porteur vérifié              | P0   | B3     | ✅ API          | Téléphone confirmé ; bénévole refusé sur commercial ; scène intime modérée                 |
| 14  | Recherche PostgreSQL et filtres                     | P0   | B3     | ✅              | `theatre` trouve `théâtre` ; p95 à mesurer sur 10 000 annonces en staging                  |
| 15  | Interface de recherche et découverte                | P0   | B3     | 🟡 web          | Filtres dans l'URL, état vide, pagination                                                  |
| 16  | Candidater, retirer, pièces jointes                 | P0   | B4     | ✅ API / ⬜ web | Une candidature par rôle                                                                   |
| 17  | Boîte des candidats et historique                   | P0   | B4     | ✅ API / ⬜ web | Chaque changement tracé avec auteur et date                                                |
| 18  | Offre, confirmation, entrée dans l'équipe           | P0   | B4     | ✅ API          | `accepted` seulement par le candidat                                                       |
| 19  | Refus automatique et délai de réponse               | P0   | B4     | ✅ API          | Un seul message par candidat ; médiane recalculée chaque nuit                              |
| 20  | Messagerie liée à la candidature                    | P0   | B5     | ✅ API / ⬜ web | Polling 15 s (`?after=`), blocage coupe la conversation, conseils affichés                 |
| 21  | Notifications in-app et e-mail                      | P0   | B5     | ✅ API / ⬜ web | Clé d'idempotence, préférences par type, heures calmes 22 h–8 h                            |
| 22  | Crédits                                             | P0   | B5     | ✅ API / ⬜ web | Crédit à un e-mail non inscrit activé à la vérification                                    |
| 23  | Signalement, blocage, file de modération            | P0   | B6     | ✅ API / ⬜ web | File priorisée, action journalisée, motivation envoyée                                     |
| 24  | Export, suppression, rétention                      | P0   | B6     | ✅ API          | Export JSON immédiat ; anonymisation immédiate, purge à 30 jours                           |
| 25  | Limitation de débit et anti-abus                    | P0   | B6     | ✅ API          | 20 candidatures / 5 annonces par jour, 429 problem+json                                    |
| 26  | Pages publiques SEO et Open Graph                   | P1   | B6     | ⬜              |                                                                                            |
| 27  | Pages légales et analytics sans cookie              | P0   | B6     | 🟡              | Version des CGU stockée à l'inscription ; pages et analytics à faire                       |
| 28  | Tests E2E, accessibilité, performance               | P0   | B6     | ⬜              | Playwright à ajouter dans `apps/web`                                                       |
| 29  | Sauvegarde, restauration, monitoring, ouverture     | P0   | B6     | ⬜              | Dépend de l'hébergeur (ADR 0005)                                                           |

## Phase L — lancement public (74 j)

| #   | Fiche                                     | Prio | État | Notes                                                                          |
| --- | ----------------------------------------- | ---- | ---- | ------------------------------------------------------------------------------ |
| 30  | Socle mobile Expo et authentification     | P0   | ⬜   | L'API accepte déjà `X-Client: mobile` (jetons dans le corps)                   |
| 31  | Écrans mobiles membre                     | P0   | ⬜   |                                                                                |
| 32  | Écrans mobiles porteur                    | P0   | ⬜   |                                                                                |
| 33  | Messagerie mobile, push, liens profonds   | P0   | ⬜   | `POST /devices` derrière `FEATURE_PUSH` ; chaque notification a un `deep_link` |
| 34  | Recherches sauvegardées, alertes, favoris | P1   | 🟡   | Modèles et endpoints derrière `FEATURE_SAVED_SEARCHES` ; tâche d'alerte prête  |
| 35  | Back-office complet                       | P1   | 🟡   | Taxonomie, communes, invitations, file, audit ; interface à faire              |
| 36  | Recours de modération                     | P0   | 🟡   | API derrière `FEATURE_APPEALS` : 30 jours, autre modérateur, réponse motivée   |
| 37  | Publication stores                        | P0   | ⬜   |                                                                                |
| 38  | Tests sur appareils réels, stabilisation  | P0   | ⬜   |                                                                                |

## Phase V1.1

Fil social (`kreo/social` : tables présentes, aucune route tant que `FEATURE_SOCIAL=false`), profils de structure, NL puis EN (clés i18n déjà alignées).
