# Infrastructure

Dossier réservé aux manifestes de déploiement (staging, production) une fois l'hébergeur choisi en sprint 0 — voir `docs/adr/0005-hebergement-staging-prod.md`.

Contraintes à respecter : données et e-mails dans l'UE, sauvegardes quotidiennes chiffrées conservées 30 jours (RPO 24 h, RTO 4 h, restauration testée chaque trimestre sur staging), sonde externe toutes les minutes, alerte si le taux d'erreur API dépasse 2 % sur 5 minutes, aucun secret dans le dépôt.
