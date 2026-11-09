# ADR 0001 — Monorepo pnpm + Turborepo

- **Statut** : accepté (sprint 0)
- **Contexte** : le cahier des charges V1.2 impose un dépôt unique pour `apps/web`, `apps/mobile`, `apps/api` et les paquets partagés `api-client`, `ui-tokens`, `i18n`, afin de ne coder qu'une fois types, tokens et traductions.
- **Décision** : monorepo pnpm (workspaces) orchestré par Turborepo. L'API Django vit dans `apps/api` avec son propre outillage Python (venv, `requirements*.txt`, ruff, pytest) ; elle n'est pas un paquet npm mais partage la CI et les conventions du dépôt.
- **Conséquences** :
  - un seul `pnpm install`, un seul `pnpm build`, cache Turborepo en CI ;
  - le contrat OpenAPI généré par l'API alimente `packages/api-client` (voir ADR 0003) ;
  - `apps/mobile` (Expo) est ajouté en phase L sans changer la structure.
