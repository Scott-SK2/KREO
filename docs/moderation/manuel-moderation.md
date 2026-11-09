# Manuel d'administration et de modération (version bêta)

## Rôles

| Rôle       | Qui                                                         | Peut                                                                                                                                                                                                                                                     |
| ---------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Modérateur | responsable de modération + suppléant, nommés avant la bêta | traiter la file des signalements, suspendre, retirer un contenu, approuver une annonce à scène intime, arbitrer un crédit contesté, lire un contenu privé **sur signalement** (lecture journalisée avec motif), voir ses propres actions dans le journal |
| Admin      | product owner                                               | tout ce qui précède + gérer taxonomie, communes, invitations bêta, consulter tout le journal d'audit, archiver un projet                                                                                                                                 |

Les droits sont portés par `users.is_moderator` et `users.is_staff` (admin Django : `/admin/`).

## File de traitement — `GET /api/v1/admin/reports`

Triée par **priorité** (1 = sécurité des personnes : harcèlement, menaces, mineurs, contenu sexuel, demande d'argent) puis par ancienneté. Délais cibles : 24 h en priorité 1, 48 h sinon. La métrique « signalements traités dans les délais » vise 95 %.

Pour chaque signalement, une action — `POST /api/v1/admin/reports/{id}/actions` :

| Action                                       | Effet                                                                           | Quand                                   |
| -------------------------------------------- | ------------------------------------------------------------------------------- | --------------------------------------- |
| `dismiss`                                    | clôt sans suite                                                                 | signalement infondé                     |
| `warn`                                       | avertissement motivé                                                            | premier écart mineur                    |
| `remove_content`                             | retire l'actualité, le message ou l'annonce (annulée), passe le projet en privé | contenu contraire à la charte           |
| `suspend_account`                            | suspension (lecture seule, sessions révoquées)                                  | abus grave ou répété                    |
| `reinstate_account`                          | rétablit                                                                        | recours accepté, erreur                 |
| `approve_opportunity` / `reject_opportunity` | valide ou refuse une annonce à scène intime                                     | file `GET /admin/opportunities/pending` |
| `arbitrate_credit`                           | trace l'arbitrage (la décision passe par `/credits/{id}/transition`)            | crédit contesté                         |

La **motivation** (≥ 20 caractères) est obligatoire : elle est envoyée à la personne concernée (e-mail obligatoire + in-app) et conservée dans `moderation_actions`. Utiliser les réponses types ci-dessous, adaptées au cas.

## Réponses types

- **Contenu retiré** : « Nous avons retiré [contenu] car il [règle enfreinte, ex. demande une participation financière aux candidats]. Tu peux le republier en corrigeant ce point. »
- **Avertissement** : « Un membre a signalé [fait]. Ce comportement est contraire à la charte (point n°X). Merci d'en tenir compte ; une récidive entraînerait une suspension. »
- **Suspension** : « Ton compte est suspendu à la suite de [faits]. Tu gardes l'accès en lecture à tes données et tu peux exporter ton compte. Tu peux faire un recours pendant 30 jours. »
- **Annonce à scène intime approuvée** : « Ton annonce est publiée : la scène intime est annoncée clairement, conformément aux règles de publication. »

## Lecture de contenu privé

Un modérateur peut ouvrir une candidature ou une conversation signalée. Chaque lecture écrit une ligne `audit_log` avec le motif (en-tête `X-Moderation-Reason`, par défaut « signalement »). Pas de lecture sans signalement.

## Recours (phase L, `FEATURE_APPEALS`)

`POST /appeals` par la personne concernée, dans les 30 jours ; traité par **un autre modérateur** (`GET /admin/appeals`, `POST /admin/appeals/{id}/decide`) avec réponse motivée. Un recours accepté sur une suspension rétablit le compte.

## Revue mensuelle

Exporter la file du mois (statuts, délais, motifs), ajuster la charte et les réponses types, consigner les changements ici.
