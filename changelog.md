# TeleScope - Changelog

Toutes les modifications notables de ce projet sont documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

---

## [Non publié]

### Ajouté
#### Frontend refonte
- Nouvelle architecture frontend (app/providers/router, features, stores, styles)
- AppShell (sidebar + header), command palette (cmdk) et raccourcis clavier
- Pages core refondues (dashboard, feed, channels, collections, search, digests, exports, settings)
- Virtualisation du feed + lazy-loading routes
- PWA (manifest + service worker)
- Tests E2E Playwright (smoke login)
#### Tests et validation
- Test de déduplication avec vector store simulé
- Tests auth refresh compatibles `httpx` récent
#### Cache Redis
- Cache persistant pour les traductions (Redis)
- Service cache centralisé (`app/services/cache.py`)
- Variables d'environnement `REDIS_URL` et `REDIS_CACHE_TTL_SECONDS`

#### Migration PostgreSQL 16
- Support PostgreSQL 16 avec driver async `asyncpg`
- Configuration Alembic pour les migrations de schéma
- Modèles adaptés pour PostgreSQL :
  - Clés primaires UUID pour toutes les tables
  - `BigInteger` pour les IDs Telegram
  - `JSONB` pour les champs structurés (media_urls, entities, filters, fetch_config)
  - Index composites optimisés pour les requêtes fréquentes
- Mode fallback SQLite pour le développement local (`USE_SQLITE=true`)

#### Authentification JWT (FastAPI-Users)
- Intégration FastAPI-Users avec support UUID
- Modèle User avec rôles RBAC (admin, analyst, viewer)
- Champs RGPD : `consent_given_at`, `data_retention_days`
- Endpoints d'authentification :
  - `POST /api/auth/register` - Inscription
  - `POST /api/auth/login` - Connexion (retourne JWT)
  - `POST /api/auth/refresh` - Rafraîchissement du token
  - `GET /api/auth/me` - Profil utilisateur
  - `POST /api/auth/me/consent` - Enregistrement consentement RGPD
  - `DELETE /api/auth/me/data` - Droit à l'oubli RGPD
- Protection de tous les endpoints avec `Depends(current_active_user)`
- Système RBAC avec permissions par rôle

#### Gestion des Flood Waits Telegram
- Décorateur `@telegram_retry` avec backoff exponentiel
- Gestion automatique des erreurs `FloodWaitError` et `SlowModeWaitError`
- Jitter aléatoire pour éviter le "thundering herd"
- Semaphore global pour limiter les requêtes parallèles (max 3 canaux)
- Auto-reconnect dans le collecteur temps réel
- Configuration via variables d'environnement :
  - `TELEGRAM_MAX_RETRIES`, `TELEGRAM_BASE_DELAY`, `TELEGRAM_MAX_DELAY`
  - `TELEGRAM_JITTER`, `TELEGRAM_CONCURRENT_CHANNELS`

#### Traduction LLM + Déduplication vectorielle
- Traduction via GPT-4o-mini avec fallback Google Translate
- Service `LLMTranslator` + facade `translator`
- Base vectorielle Qdrant + embeddings `sentence-transformers`
- Déduplication sémantique (cosine) avec `embedding_id` stocké en base
- Variables d'environnement OpenAI/Qdrant ajoutées

### Modifié
- `app/services/vector_store.py` - intégration Qdrant + import lazy des embeddings
- `app/schemas/*` - passage à `ConfigDict` pour Pydantic v2
- `requirements.txt` - ajout de `qdrant-client`, `redis`
- `config.py` - Ajout de toutes les configurations (PostgreSQL, JWT, Telegram rate limiting)
- `database.py` - Support dual SQLite/PostgreSQL avec engine factory
- Modèles Channel, Message, Summary - Adaptation UUID et types PostgreSQL
- Endpoints channels, messages, summaries - Protection JWT obligatoire
- `telegram_collector.py` - Décorateur retry sur toutes les méthodes
- `realtime_collector.py` - Boucle auto-reconnect avec gestion des erreurs
- `docker-compose.yml` - Ajout Redis + Qdrant aligné sur le client
- `config.py` - Ignore les variables `.env` non utilisées pour éviter les erreurs Alembic

### Corrigé
- Migration initiale Alembic réécrite pour une création clean du schéma
- Comparaison timezone-safe des refresh tokens
- Champs `metadata` renommés côté ORM (`metadata_json`) pour éviter les conflits SQLAlchemy

### Supprimé
- Fichier SQLite local versionné par erreur (`backend/data/telescope.db` et WAL/SHM)

### Sécurité
- Authentification JWT obligatoire sur tous les endpoints
- Tokens signés avec `HS256`, expiration configurable
- Soft-delete pour les canaux (désactivation au lieu de suppression)
- Logging des tentatives de connexion et erreurs

---

## [0.1.0] - 2026-01-16

### Ajouté
- **Création du dépôt** - Structure initiale du projet TeleScope
- **Project Spec** - Document de spécifications complet (`project_spec.md`)
  - Définition des personas utilisateurs (journalistes, analystes, responsables veille)
  - Spécifications des fonctionnalités MVP (traduction LLM, déduplication, digests)
  - Architecture technique cible détaillée
  - Roadmap avec 3 milestones
- **Prototype fonctionnel** - Première version de l'application
  - Backend FastAPI avec SQLite (mode WAL)
  - Collecteur Telegram via Telethon
  - Traduction via Google Translate (deep-translator)
  - Déduplication basique (SequenceMatcher)
  - Service de résumés
  - Frontend React 18 avec Vite
- **Documentation**
  - `CLAUDE.md` - Mémoire contextuelle du projet
  - `architecture.md` - Architecture technique actuelle et cible
  - `project_status.md` - État d'avancement du projet
  - `changelog.md` - Historique des modifications

### Stack Technique Initiale
| Composant | Technologie |
|-----------|-------------|
| Backend | FastAPI |
| Base de données | SQLite (WAL) |
| Collecteur Telegram | Telethon |
| Traduction | Google Translate |
| Déduplication | SequenceMatcher |
| Frontend | React 18 + Vite |

---

## Format des Entrées

### Types de changements
- **Ajouté** - Nouvelles fonctionnalités
- **Modifié** - Changements dans les fonctionnalités existantes
- **Déprécié** - Fonctionnalités qui seront supprimées prochainement
- **Supprimé** - Fonctionnalités supprimées
- **Corrigé** - Corrections de bugs
- **Sécurité** - Corrections de vulnérabilités

### Convention de versioning
- **MAJOR** (X.0.0) - Changements incompatibles avec les versions précédentes
- **MINOR** (0.X.0) - Nouvelles fonctionnalités rétrocompatibles
- **PATCH** (0.0.X) - Corrections de bugs rétrocompatibles

---

**Voir aussi:** [project_spec.md](./project_spec.md) | [architecture.md](./architecture.md) | [project_status.md](./project_status.md)
