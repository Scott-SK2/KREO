# ADR 0006 — Services métier transactionnels, machine à états et permissions objet par objet

- **Statut** : accepté
- **Décision** : chaque domaine déclare ses transitions dans un `StateMachine` (`kreo/common/transitions.py`) : états source, état cible, rôles autorisés, garde optionnelle. Le service (`transition_project`, `transition_opportunity`, `transition_application`, `transition_credit`) verrouille la ligne (`SELECT … FOR UPDATE`), vérifie le rôle de l'acteur, écrit l'événement d'historique, déclenche les effets (fermeture des annonces, refus automatiques, création du membre d'équipe) et les notifications, le tout dans une transaction.
- **Rôles** : `visitor`, `member` (compte), `owner` (porteur), `manager` (co-organisateur), `team_member` (membre d'équipe), `moderator`, `admin`. Les permissions sont vérifiées côté API, objet par objet ; l'interface ne fait que masquer.
- **Blocage** : appliqué partout (recherche, candidatures, messagerie, profils). Toute lecture de contenu privé par un modérateur est journalisée avec son motif (`audit_log`).
