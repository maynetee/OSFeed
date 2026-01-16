# TeleScope - Architecture Technique

**Version:** 1.0
**Dernière mise à jour:** 2026-01-16 18:40

---

## Table des Matières

1. [Architecture Actuelle (Prototype)](#1-architecture-actuelle-prototype)
2. [Architecture Cible (MVP)](#2-architecture-cible-mvp)
3. [Pipeline de Traitement](#3-pipeline-de-traitement)
4. [Schéma de Migration](#4-schéma-de-migration)

---

## 1. Architecture Actuelle (Prototype)

### 1.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE ACTUELLE (Prototype)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌──────────────┐     ┌──────────────┐     ┌──────────────┐          │
│    │   Telegram   │────▶│   Telethon   │────▶│   SQLite     │          │
│    │   Channels   │     │  (Collector) │     │   (WAL)      │          │
│    └──────────────┘     └──────────────┘     └──────┬───────┘          │
│                               │                      │                  │
│                               ▼                      │                  │
│                        ┌──────────────┐              │                  │
│                        │   Google     │              │                  │
│                        │  Translate   │              │                  │
│                        │(deep-transl.)│              │                  │
│                        └──────────────┘              │                  │
│                                                      │                  │
│    ┌──────────────┐     ┌──────────────┐     ┌──────┴───────┐          │
│    │    React     │◀────│   FastAPI    │◀────│ SQLAlchemy   │          │
│    │   Frontend   │     │    (REST)    │     │   (Async)    │          │
│    └──────────────┘     └──────────────┘     └──────────────┘          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Composants Actuels

| Composant | Technologie | Fichier Principal | Statut |
|-----------|-------------|-------------------|--------|
| Base de données | **PostgreSQL 16** (+ SQLite fallback) | `backend/app/database.py` | **Migré** |
| Migrations | **Alembic** (async) | `backend/alembic/` | **Nouveau** |
| Authentification | **FastAPI-Users + JWT** | `backend/app/auth/` | **Nouveau** |
| Collecteur Telegram | Telethon + **retry backoff** | `backend/app/services/telegram_collector.py` | **Amélioré** |
| Collecteur temps réel | Telethon + **auto-reconnect** | `backend/app/services/realtime_collector.py` | **Amélioré** |
| Retry Utilities | **Décorateur @telegram_retry** | `backend/app/utils/retry.py` | **Nouveau** |
| Traduction | GPT-4o-mini + fallback Google Translate | `backend/app/services/llm_translator.py` | **Nouveau** |
| Cache | Redis (traductions persistantes) | `backend/app/services/cache.py` | **Nouveau** |
| Déduplication | Qdrant (cosine) | `backend/app/services/deduplicator.py` | **Nouveau** |
| Résumés | Service interne | `backend/app/services/summarizer.py` | - |
| API REST | FastAPI + **Auth obligatoire** | `backend/app/main.py` | **Amélioré** |
| Frontend | React 18 + Vite 5 + Tailwind | `frontend/` | **Refonte UI** |

### 1.3 Structure des Fichiers Backend

```
backend/
├── alembic/                    # [NOUVEAU] Migrations PostgreSQL
│   ├── versions/               # Fichiers de migration
│   ├── env.py                  # Configuration async
│   └── script.py.mako          # Template migrations
├── alembic.ini                 # Configuration Alembic
├── app/
│   ├── api/
│   │   ├── auth.py             # [NOUVEAU] Endpoints authentification
│   │   ├── channels.py         # Endpoints canaux (protégé JWT)
│   │   ├── messages.py         # Endpoints messages (protégé JWT)
│   │   └── summaries.py        # Endpoints résumés (protégé JWT)
│   ├── auth/                   # [NOUVEAU] Package authentification
│   │   ├── __init__.py
│   │   ├── users.py            # Configuration FastAPI-Users
│   │   └── rbac.py             # Permissions par rôle
│   ├── models/
│   │   ├── channel.py          # Modèle Channel (UUID, BigInteger)
│   │   ├── message.py          # Modèle Message (UUID, JSONB)
│   │   ├── summary.py          # Modèle Summary (UUID, JSONB)
│   │   └── user.py             # [NOUVEAU] Modèle User (RBAC)
│   ├── schemas/
│   │   ├── channel.py          # Schémas Pydantic (UUID)
│   │   ├── message.py          # Schémas Pydantic (UUID)
│   │   ├── summary.py          # Schémas Pydantic (UUID)
│   │   └── user.py             # [NOUVEAU] Schémas User
│   ├── services/
│   │   ├── telegram_collector.py  # Collecte + @telegram_retry
│   │   ├── realtime_collector.py  # Temps réel + auto-reconnect
│   │   ├── translator.py          # Facade traduction LLM
│   │   ├── llm_translator.py      # GPT-4o-mini + fallback
│   │   ├── cache.py               # Cache Redis (traductions)
│   │   ├── vector_store.py        # Qdrant + embeddings
│   │   ├── deduplicator.py        # Déduplication vectorielle
│   │   └── summarizer.py          # Génération résumés
│   ├── utils/                  # [NOUVEAU] Utilitaires
│   │   ├── __init__.py
│   │   └── retry.py            # Décorateur @telegram_retry
│   ├── jobs/
│   │   ├── collect_messages.py    # Job de collecte
│   │   └── generate_summaries.py  # Job de résumés
│   ├── config.py               # Configuration (PostgreSQL, JWT, Telegram)
│   ├── database.py             # Connexion PostgreSQL/SQLite
│   └── main.py                 # Application FastAPI + auth router
├── scripts/                    # Scripts utilitaires
│   ├── check_postgres.py        # Vérif connexion + tables
│   └── migrate_sqlite_to_postgres.py  # Migration SQLite → PostgreSQL
└── requirements.txt            # Dépendances mises à jour
```

### 1.4 Frontend Refonte (Vite + React)

```
frontend/
├── src/
│   ├── app/                 # Providers + routing
│   ├── components/          # UI + layout + domain components
│   ├── features/            # Pages par feature
│   ├── hooks/               # Hooks globaux
│   ├── lib/                 # API client + utils
│   ├── stores/              # Zustand stores
│   └── styles/              # Global styles + theme
├── public/                  # PWA assets
├── vite.config.ts
└── components.json          # config shadcn/ui
```

**Points clés** :
- React Router 6 + routes lazy-load
- Zustand (UI / filters / user)
- TanStack Query (server state)
- Command palette (cmdk) + raccourcis clavier
- Virtualisation du feed + PWA + tests E2E (Playwright)

### 1.5 Limitations Identifiées (Mises à jour)

| Limitation | Impact | Composant | Statut |
|------------|--------|-----------|--------|
| ~~SQLite single-writer~~ | ~~Pas de scaling horizontal~~ | `database.py` | **RÉSOLU** - PostgreSQL 16 |
| ~~Déduplication O(n²)~~ | ~~Lenteur à 10K+ messages~~ | `deduplicator.py` | **RÉSOLU** - Qdrant |
| ~~Google Translate~~ | ~~Instable, pas de contexte OSINT~~ | `translator.py` | **RÉSOLU** - GPT-4o-mini |
| ~~Telethon lock global~~ | ~~Collecte sérialisée~~ | `telegram_collector.py` | **AMÉLIORÉ** - retry + semaphore |
| ~~Pas d'authentification~~ | ~~Données accessibles à tous~~ | - | **RÉSOLU** - JWT + RBAC |
| Pas de logs d'audit | Non conforme RGPD | - | **PARTIEL** - audit_logs + endpoints |
| Cache en mémoire | Perdu au redémarrage | `translator.py` | **RÉSOLU** - Redis |

---

## 2. Architecture Cible (MVP)

### 2.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                        ARCHITECTURE CIBLE - MVP                                  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐    │
│  │                         COUCHE COLLECTE                                  │    │
│  │  ┌──────────┐   ┌──────────┐   ┌──────────┐                             │    │
│  │  │Collector │   │Collector │   │Collector │  (Workers indépendants)     │    │
│  │  │Worker 1  │   │Worker 2  │   │Worker N  │                             │    │
│  │  └────┬─────┘   └────┬─────┘   └────┬─────┘                             │    │
│  │       │              │              │                                    │    │
│  │       └──────────────┼──────────────┘                                    │    │
│  │                      ▼                                                   │    │
│  │              ┌───────────────┐                                           │    │
│  │              │ Redis Queue   │  (Buffer + Rate limiting)                 │    │
│  │              │ (ARQ/Celery)  │                                           │    │
│  │              └───────┬───────┘                                           │    │
│  └──────────────────────┼───────────────────────────────────────────────────┘    │
│                         │                                                        │
│  ┌──────────────────────┼───────────────────────────────────────────────────┐    │
│  │                      ▼         COUCHE TRAITEMENT                          │    │
│  │              ┌───────────────┐                                            │    │
│  │              │ Processing    │                                            │    │
│  │              │ Pipeline      │                                            │    │
│  │              └───────┬───────┘                                            │    │
│  │                      │                                                    │    │
│  │     ┌────────────────┼────────────────┐                                   │    │
│  │     ▼                ▼                ▼                                   │    │
│  │ ┌────────┐    ┌────────────┐    ┌──────────┐                             │    │
│  │ │  LLM   │    │  Embedding │    │  Entity  │                             │    │
│  │ │Transl. │    │ Generation │    │Extraction│                             │    │
│  │ │GPT-4o  │    │text-embed  │    │  (NER)   │                             │    │
│  │ │-mini   │    │-3-small    │    │          │                             │    │
│  │ └───┬────┘    └─────┬──────┘    └────┬─────┘                             │    │
│  └─────┼───────────────┼────────────────┼────────────────────────────────────┘    │
│        │               │                │                                        │
│  ┌─────┼───────────────┼────────────────┼────────────────────────────────────┐    │
│  │     ▼               ▼                ▼         COUCHE STOCKAGE            │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                   PostgreSQL 16                       │                  │    │
│  │ │  - Messages (texte, métadonnées, traductions)        │                  │    │
│  │ │  - Channels                                          │                  │    │
│  │ │  - Users & Auth                                      │                  │    │
│  │ │  - Audit Logs (RGPD)                                 │                  │    │
│  │ │  - Full-text search (tsvector)                       │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  │                                                                           │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                      Qdrant                           │                  │    │
│  │ │  - Embeddings vectoriels (déduplication O(log n))    │                  │    │
│  │ │  - Index de recherche sémantique                     │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  │                                                                           │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                      Redis                            │                  │    │
│  │ │  - Cache traductions (persistant)                    │                  │    │
│  │ │  - Session store                                     │                  │    │
│  │ │  - Rate limiting Telegram                            │                  │    │
│  │ │  - File d'attente (ARQ/Celery)                       │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  └───────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐    │
│  │                         COUCHE API                                         │    │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │    │
│  │   │   FastAPI    │    │   Auth       │    │   Rate       │                │    │
│  │   │   REST API   │◀──▶│   (JWT)      │◀──▶│   Limiter    │                │    │
│  │   └──────┬───────┘    └──────────────┘    └──────────────┘                │    │
│  └──────────┼─────────────────────────────────────────────────────────────────┘    │
│             │                                                                      │
│  ┌──────────┼─────────────────────────────────────────────────────────────────┐    │
│  │          ▼                   COUCHE PRÉSENTATION                           │    │
│  │   ┌──────────────────────────────────────────────────────────────────┐    │    │
│  │   │                     React SPA (Vite + TailwindCSS)                │    │    │
│  │   │  - Dashboard avec KPIs                                           │    │    │
│  │   │  - Feed messages avec filtres                                    │    │    │
│  │   │  - Gestion canaux & collections                                  │    │    │
│  │   │  - Daily Digests                                                 │    │    │
│  │   │  - Export (PDF, CSV)                                             │    │    │
│  │   └──────────────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Stack Technique Cible

| Composant | Actuel | Cible | Justification |
|-----------|--------|-------|---------------|
| Base relationnelle | SQLite | **PostgreSQL 16** | Multi-writer, JSONB, extensions |
| Base vectorielle | - | **Qdrant** | Déduplication O(log n), recherche sémantique |
| Cache/Queue | Mémoire | **Redis 7** | Persistance, sessions, rate limiting |
| Traduction | **GPT-4o-mini + fallback** | **GPT-4o-mini** | Contexte OSINT, coût réduit |
| Embeddings | **sentence-transformers/all-MiniLM-L6-v2** | **sentence-transformers/all-MiniLM-L6-v2** | Déduplication sémantique |
| Task Queue | - | **ARQ** (ou Celery) | Jobs distribués, retry, monitoring |
| Auth | - | **FastAPI-Users + JWT** | OAuth2, sessions, RBAC |

### 2.3 Améliorations Clés

| Aspect | Avant | Après |
|--------|-------|-------|
| Déduplication | O(n²) - SequenceMatcher | O(log n) - Index vectoriel Qdrant |
| Scaling | Single-writer SQLite | Multi-writer PostgreSQL |
| Traduction | Google (générique) | GPT-4o-mini (contexte OSINT) |
| Cache | Mémoire (volatile) | Redis (persistant) |
| Sécurité | Aucune auth | JWT + RBAC |
| Conformité | Non RGPD | Audit logs + consentement |

---

## 3. Pipeline de Traitement

### 3.1 Flux de Données Cible

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE DE TRAITEMENT                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  1. INGESTION           2. ENRICHISSEMENT         3. INDEXATION         │
│  ┌───────────┐          ┌───────────────┐         ┌───────────────┐    │
│  │           │          │               │         │               │    │
│  │ Message   │─────────▶│ Détection     │────────▶│ PostgreSQL    │    │
│  │ Telegram  │          │ langue        │         │ (métadonnées) │    │
│  │           │          │               │         │               │    │
│  └───────────┘          └───────┬───────┘         └───────────────┘    │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐         ┌───────────────┐    │
│                         │               │         │               │    │
│                         │ Traduction    │────────▶│ Redis Cache   │    │
│                         │ GPT-4o-mini   │         │ (TTL 7 jours) │    │
│                         │               │         │               │    │
│                         └───────┬───────┘         └───────────────┘    │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐         ┌───────────────┐    │
│                         │               │         │               │    │
│                         │ Embedding     │────────▶│ Qdrant        │    │
│                         │ text-embed-3  │         │ (vecteurs)    │    │
│                         │               │         │               │    │
│                         └───────┬───────┘         └───────────────┘    │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐                              │
│                         │               │                              │
│                         │ Déduplication │──▶ Score originalité (0-100) │
│                         │ Sémantique    │                              │
│                         │               │                              │
│                         └───────┬───────┘                              │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐                              │
│                         │               │                              │
│                         │ NER           │──▶ Entités (personnes,       │
│                         │ (Extraction)  │     lieux, organisations)    │
│                         │               │                              │
│                         └───────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Gestion des Flood Waits Telegram

```python
# Stratégie de retry avec exponential backoff
async def fetch_with_backoff(channel_id: int, limit: int = 100):
    for attempt in range(max_retries):
        try:
            jitter = random.uniform(0.5, 1.5)
            await asyncio.sleep(base_delay * jitter)
            return await client.get_messages(channel_id, limit=limit)
        except FloodWaitError as e:
            wait_time = e.seconds + random.uniform(1, 5)
            await asyncio.sleep(wait_time)
    raise Exception("Max retries exceeded")
```

---

## 4. Schéma de Migration

### 4.1 Ordre des Migrations

```
Étape 1: Migration PostgreSQL ✅ FAIT
    └── [x] SQLite → PostgreSQL 16 (schéma v2 avec UUID, JSONB)
    └── [x] Alembic configuré pour migrations async
    └── [x] Fallback SQLite pour développement local
    └── [x] Script migration SQLite → PostgreSQL (`backend/scripts/migrate_sqlite_to_postgres.py`)

Étape 2: Authentification ✅ FAIT
    └── [x] FastAPI-Users + JWT
    └── [x] RBAC (admin, analyst, viewer)
    └── [x] Protection tous endpoints
    └── [x] Champs RGPD (consentement, rétention)

Étape 3: Gestion Flood Waits ✅ FAIT
    └── [x] Décorateur @telegram_retry
    └── [x] Backoff exponentiel + jitter
    └── [x] Semaphore pour concurrence limitée
    └── [x] Auto-reconnect collecteur temps réel

Étape 4: Intégration Redis ⏳ À FAIRE
    └── [ ] Cache traductions
    └── [ ] Sessions utilisateur
    └── [ ] Rate limiting distribué

Étape 5: Base Vectorielle ✅ FAIT
    └── [x] Qdrant setup (code)
    └── [x] Migration embeddings (au fil de l'eau)
    └── [x] Déduplication sémantique

Étape 6: Traduction LLM ✅ FAIT
    └── [x] GPT-4o-mini integration
    └── [x] Prompts OSINT spécialisés

Étape 7: Tâches de Fond ⏳ À FAIRE
    └── [ ] ARQ ou Celery
    └── [ ] Jobs de collecte/digest distribués
```

### 4.2 Runbook Migration SQLite → PostgreSQL

1) Démarrer PostgreSQL (Docker)
```
docker compose up -d
```

2) Appliquer les migrations Alembic
```
cd backend
alembic upgrade head
```

3) Migrer les données SQLite (optionnel)
```
python3 scripts/migrate_sqlite_to_postgres.py --dry-run
python3 scripts/migrate_sqlite_to_postgres.py
```

4) Vérifier la connexion et le schéma
```
python3 scripts/check_postgres.py
```

### 4.3 Structure Cible des Fichiers

```
telescope/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   │   ├── auth.py
│   │   │   ├── channels.py
│   │   │   ├── collections.py
│   │   │   ├── messages.py
│   │   │   ├── digests.py
│   │   │   └── export.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   ├── models/
│   │   ├── schemas/
│   │   ├── services/
│   │   │   ├── telegram/
│   │   │   ├── llm/
│   │   │   ├── vector/
│   │   │   └── audit.py
│   │   ├── jobs/
│   │   └── main.py
│   ├── alembic/
│   └── tests/
├── frontend/
├── docker-compose.yml
└── README.md
```

---

**Document maintenu par l'équipe technique**
**Voir aussi:** [project_spec.md](./project_spec.md) | [project_status.md](./project_status.md) | [changelog.md](./changelog.md)
