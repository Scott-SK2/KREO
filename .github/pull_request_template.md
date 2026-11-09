## Fiche du backlog

<!-- Numéro et titre de la fiche (docs/backlog.md), ou « hors backlog » avec le pourquoi. -->

## Ce que change cette PR

## Définition de terminé

- [ ] Code revu par l'autre développeur
- [ ] Migrations rejouables à vide (`makemigrations --check`, `migrate` sur base vide)
- [ ] Contrôle d'accès testé : cas autorisé **et** cas refusé
- [ ] Tests unitaires et API verts ; E2E du parcours concerné vert
- [ ] Accessibilité vérifiée (clavier, focus visible, contraste AA, cibles ≥ 44 px) ; responsive validé
- [ ] Aucune donnée personnelle dans les journaux
- [ ] Documentation OpenAPI à jour (`packages/api-client/openapi.json` régénéré si l'API change)
- [ ] Retour arrière possible (migration réversible, feature flag si besoin)
- [ ] Chaînes dans `@kreo/i18n`, aucune chaîne en dur
