# TeleScope - Mémoire Contextuelle

## Vision

Transformer TeleScope en **outil de renseignement opérationnel** destiné aux journalistes d'investigation et analystes OSINT. L'objectif est de fournir une plateforme capable de collecter, analyser et synthétiser des informations provenant de canaux Telegram pour faciliter le travail d'enquête.

## Stack Technique Cible

| Composant | Technologie |
|-----------|-------------|
| Backend API | FastAPI |
| Base de données | PostgreSQL 16 |
| Base vectorielle | Qdrant |
| LLM | GPT-4o-mini |
| Cache | Redis |
| Frontend | React 18 |
| Tâches de fond | ARQ ou Celery |

## Frontend (refonte)

- Vite 5 + React 18 + React Router 6
- Tailwind CSS + shadcn/ui + cmdk
- Zustand (state client) + TanStack Query (state serveur)
- PWA + tests E2E (Playwright)

## Règles de Dépôt

- **Ne jamais pousser directement sur `main`** - Toute modification doit passer par une Pull Request
- **Branches par fonctionnalité** - Utiliser le format `feature/<nom-fonctionnalité>` ou `fix/<nom-bug>`
- **Tâches de fond** - Utiliser ARQ (recommandé pour async) ou Celery pour tout traitement long ou planifié
- **Code review obligatoire** - Au moins une approbation avant merge

## Documentation

- [project_spec.md](./project_spec.md) - Spécifications détaillées du projet
- [architecture.md](./architecture.md) - Architecture technique actuelle et cible
- [project_status.md](./project_status.md) - État d'avancement du projet
- [changelog.md](./changelog.md) - Historique des modifications
- [FRONTEND_REFONTE.md](./FRONTEND_REFONTE.md) - Plan de refonte frontend
- [api.md](./api.md) - Documentation API (à créer)

## Mise à Jour de la Documentation

**IMPORTANT** : Après chaque fonctionnalité terminée, mettre à jour (avec date et heure) les fichiers suivants :

1. **changelog.md** - Ajouter une entrée décrivant la fonctionnalité :
   - Utiliser les catégories : Ajouté, Modifié, Corrigé, Supprimé, Sécurité
   - Inclure les détails techniques pertinents

2. **project_status.md** - Mettre à jour (avec date et heure) :
   - Le statut des tâches dans la section du jalon en cours
   - Les métriques si applicables
   - Les risques/blocages si changement

3. **architecture.md** - Mettre à jour (avec date et heure) si :
   - Nouvelle technologie ajoutée
   - Changement de structure des fichiers
   - Modification du pipeline de données

## Instructions de Test

### Avant toute validation de PR

1. **Vérifier la collecte Telegram** - S'assurer que le système gère correctement les **Flood Waits** de l'API Telegram
2. Tester les scénarios de rate limiting
3. Valider que les reconnexions automatiques fonctionnent
4. Vérifier les logs pour détecter tout avertissement Telegram

```bash
# Exemple de vérification des Flood Waits dans les logs
grep -i "flood" logs/*.log
```

## Conventions

- Langue du code : Anglais
- Langue de la documentation : Français
- Commits : Format conventionnel (`feat:`, `fix:`, `docs:`, etc.)
