# ADR 0005 — Hébergement, environnements et déploiement (à finaliser en sprint 0)

- **Statut** : proposé
- **Contraintes** (cahier des charges) : données hébergées dans l'UE, e-mail transactionnel UE, analytics sans cookie UE, sauvegardes quotidiennes chiffrées conservées 30 jours (RPO 24 h, RTO 4 h), disponibilité 99,5 %, secrets hors dépôt.
- **Proposition** : PostgreSQL et Redis managés en région UE ; API et worker Celery en conteneurs (Dockerfile fourni dans `apps/api`) ; web Next.js sur un hébergeur edge avec région UE ; médias sur Cloudflare R2 ; Sentry (région UE) ; sonde externe toutes les minutes.
- **Environnements** : `local` (docker compose + jeu de démonstration `seed_demo`), `staging` (données fictives, déploiement automatique à chaque fusion sur `main`), `production` (accès nominatifs et journalisés).
- **À décider** : hébergeur précis et budget mensuel (question ouverte du cahier des charges). Le job `deploy-staging` de la CI est prêt à recevoir le hook.
