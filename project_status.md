# TeleScope - État du Projet

**Dernière mise à jour:** 2026-01-16 18:40

---

## Statut Global

| Indicateur | Valeur |
|------------|--------|
| **Phase actuelle** | Build M1 |
| **Milestone** | M1 - MVP de Niche |
| **Prochain jalon** | Tests d'intégration et première migration |
| **Blocages** | Aucun |

---

## 1. État Actuel : Prototype Validé

### 1.1 Ce qui fonctionne

| Fonctionnalité | Statut | Notes |
|----------------|--------|-------|
| Collecte Telegram | OK | Via Telethon, single-thread |
| Traduction automatique | OK | GPT-4o-mini + fallback Google Translate |
| Déduplication messages | OK | Qdrant (cosine) + embeddings |
| Résumés automatiques | OK | Service interne |
| API REST | OK | FastAPI |
| Interface utilisateur | OK | React 18 + Vite |
| Persistance données | OK | PostgreSQL 16 (+ SQLite fallback) |
| Cache traductions | OK | Redis (optionnel) |
| Frontend refonte | OK | AppShell, feed virtualise, cmd palette, PWA |

### 1.2 Limitations connues

| Limitation | Impact | Priorité | Statut |
|------------|--------|----------|--------|
| SQLite single-writer | Pas de scaling | P0 | ✅ Résolu (PostgreSQL) |
| Pas d'authentification | Données publiques | P0 | ✅ Résolu (JWT) |
| Pas de gestion FloodWait | Ban Telegram | P0 | ✅ Résolu (backoff) |
| ~~Déduplication O(n²)~~ | ~~Lent à 10K+ messages~~ | P0 | ✅ Résolu (Qdrant) |
| ~~Google Translate générique~~ | ~~Traductions imprécises~~ | P1 | ✅ Résolu (GPT-4o-mini) |
| Cache mémoire volatile | Perte au redémarrage | P1 | ✅ Résolu (Redis) |
| Pas d'audit logs | Non conforme RGPD | P2 | 🟡 Partiel (audit_logs + endpoints) |

---

## 2. Prochain Jalon : Migration PostgreSQL

### 2.1 Objectif

Remplacer SQLite par PostgreSQL 16 pour permettre le scaling horizontal et préparer l'intégration des fonctionnalités MVP.

### 2.2 Tâches

| Tâche | Statut | Notes |
|-------|--------|-------|
| Configurer PostgreSQL local | **Fait** | Via docker ou installation locale |
| Adapter le schéma de données | **Fait** | UUID, BigInteger, JSONB |
| Configurer Alembic (migrations) | **Fait** | `backend/alembic/` configuré |
| Migrer les données existantes | **Fait (script)** | `backend/scripts/migrate_sqlite_to_postgres.py` |
| Adapter les requêtes SQLAlchemy | **Fait** | Endpoints mis à jour |
| Tests de régression | **Fait** | `pytest` |
| Mise à jour docker-compose | **Fait** | `docker-compose.yml` ajouté |

### 2.3 Critères d'acceptation

- [x] Configuration PostgreSQL 16 prête
- [x] Schéma de données adapté (UUID, JSONB)
- [x] Migrations Alembic configurées
- [x] Tests passent
- [x] Documentation mise à jour

---

## 3. Roadmap M1 - MVP de Niche

### 3.1 Vue d'ensemble

```
Migration    Authentification    Traduction    Base         Daily
PostgreSQL → JWT               → LLM        → Vectorielle → Digests v2
   │              │                 │             │             │
   ▼              ▼                 ▼             ▼             ▼
  [FAIT]        [FAIT]         [FAIT]       [FAIT]       [FAIT]
```

### 3.2 Fonctionnalités M1

| Fonctionnalité | Priorité | Statut | Dépendances |
|----------------|----------|--------|-------------|
| Migration PostgreSQL | P0 | ✅ **Fait** | - |
| Authentification JWT | P0 | ✅ **Fait** | PostgreSQL |
| Flood Wait handling | P0 | ✅ **Fait** | - |
| Traduction LLM (GPT-4o-mini) | P0 | ✅ **Fait (code)** | - |
| Base vectorielle (Qdrant) | P0 | ✅ **Fait (code)** | - |
| Déduplication sémantique | P0 | ✅ **Fait (code)** | Qdrant |
| Daily Digests v2 | P1 | ✅ **Fait** | Traduction LLM |
| Collections de canaux | P1 | ✅ **Fait** | PostgreSQL |
| Dashboard KPIs | P1 | ✅ **Fait** | PostgreSQL |
| Export CSV/PDF | P2 | ✅ **Fait** | - |
| Audit logs RGPD | P2 | 🟡 **Partiel** | PostgreSQL |
| Frontend refonte | P0 | ✅ **Fait** | Pages core + features |

---

### 3.3 Checklist détaillée M1

#### 🗄️ Migration PostgreSQL
- [x] Ajouter dépendances `asyncpg`, `alembic` dans requirements.txt
- [x] Configurer `config.py` avec paramètres PostgreSQL
- [x] Implémenter engine factory dual SQLite/PostgreSQL dans `database.py`
- [x] Adapter modèle `Channel` (UUID, BigInteger, JSON)
- [x] Adapter modèle `Message` (UUID, BigInteger, JSON, index composites)
- [x] Adapter modèle `Summary` (UUID, JSON)
- [x] Configurer Alembic (`alembic/env.py` async)
- [x] Créer migration initiale
- [x] Tester avec SQLite (`USE_SQLITE=true`)
- [x] Tester avec PostgreSQL réel
- [x] Script migration données SQLite → PostgreSQL (`backend/scripts/migrate_sqlite_to_postgres.py`)
- [x] Mettre à jour docker-compose (`docker-compose.yml`)

#### 🔐 Authentification JWT (FastAPI-Users)
- [x] Ajouter dépendances `fastapi-users[sqlalchemy]`, `passlib`, `python-jose`
- [x] Créer modèle `User` avec RBAC (admin/analyst/viewer)
- [x] Créer schémas Pydantic `UserCreate`, `UserRead`, `UserUpdate`
- [x] Configurer FastAPI-Users (`auth/users.py`)
- [x] Implémenter système RBAC (`auth/rbac.py`)
- [x] Créer router authentification (`api/auth.py`)
- [x] Ajouter endpoints RGPD (consent, data deletion)
- [x] Protéger endpoint `/api/channels` avec JWT
- [x] Protéger endpoint `/api/messages` avec JWT
- [x] Protéger endpoint `/api/summaries` avec JWT
- [x] Tester inscription utilisateur
- [x] Tester login et génération token
- [x] Tester rejet requêtes sans token
- [x] Tester refresh token
- [x] Tests unitaires auth

#### ⏱️ Gestion Flood Waits Telegram
- [x] Ajouter dépendance `tenacity`
- [x] Configurer paramètres retry dans `config.py`
- [x] Créer décorateur `@telegram_retry` (`utils/retry.py`)
- [x] Implémenter backoff exponentiel avec jitter
- [x] Implémenter semaphore pour limiter concurrence (max 3 canaux)
- [x] Appliquer `@telegram_retry` sur `TelegramCollector`
- [x] Ajouter auto-reconnect dans `RealtimeCollector`
- [ ] Tester en conditions réelles avec credentials Telegram
- [ ] Vérifier logs FloodWait après 24h de collecte

#### 🌐 Traduction LLM (GPT-4o-mini)
- [x] Ajouter dépendance `openai`
- [x] Configurer clé API OpenAI dans `.env` (exemple)
- [x] Créer service `LLMTranslator` (`services/llm_translator.py`)
- [x] Implémenter prompt optimisé pour contexte OSINT
- [x] Ajouter cache traductions (Redis)
- [x] Fallback vers Google Translate si erreur
- [x] Remplacer deep-translator par LLM dans pipeline
- [x] Monitoring coûts API

#### 🔍 Base vectorielle (Qdrant)
- [x] Ajouter service Qdrant dans `docker-compose.yml`
- [x] Démarrer Qdrant (local)
- [x] Ajouter dépendances `qdrant-client`, `sentence-transformers`
- [x] Configurer collection Qdrant dans `.env` (exemple)
- [x] Créer service `VectorStore` (`services/vector_store.py`)
- [x] Implémenter génération embeddings
- [x] Implémenter upsert/query Qdrant
- [x] Stocker `embedding_id` dans table messages
- [ ] Tester recherche sémantique

#### 🔄 Déduplication sémantique
- [x] Implémenter calcul similarité cosinus via Qdrant
- [x] Définir seuil de similarité (ex: 0.85)
- [x] Marquer messages dupliqués (`is_duplicate=True`)
- [x] Grouper duplicats (`duplicate_group_id`)
- [x] Calculer `originality_score`
- [x] Remplacer SequenceMatcher par déduplication vectorielle
- [x] Tester avec corpus de messages similaires

#### 📰 Daily Digests v2
- [x] Améliorer prompt de génération de résumés
- [x] Utiliser GPT-4o-mini pour synthèse
- [x] Filtrer duplicats avant génération
- [x] Ajouter section "entités clés" (personnes, lieux)
- [x] Générer version HTML pour email
- [x] Scheduler génération quotidienne (08:00)
- [x] Associer digests aux utilisateurs

#### 📁 Collections de canaux (P1)
- [x] Créer modèle `Collection`
- [x] Créer endpoints CRUD collections
- [x] Permettre filtrage par collection dans digests
- [x] UI pour gérer collections

#### 📊 Dashboard KPIs (P1)
- [x] Endpoint stats globales (messages/jour, canaux actifs)
- [x] Endpoint stats par canal
- [x] UI dashboard avec graphiques
- [x] Export métriques

#### 📤 Export CSV/PDF (P2)
- [x] Endpoint export messages CSV
- [x] Endpoint export digest PDF
- [x] UI boutons export

#### 📋 Audit logs RGPD (P2)
- [x] Créer modèle `AuditLog`
- [x] Logger actions utilisateur
- [x] Endpoint consultation logs
- [x] Rétention configurable

---

## 4. Risques et Blocages

### 4.1 Risques actuels

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| Ban compte Telegram | Haute | Critique | Rate limiting strict, multi-comptes |
| Coûts LLM élevés | Moyenne | Haute | Monitoring usage, cache agressif |

### 4.2 Blocages

*Aucun blocage actuel.*

---

## 5. Décisions Techniques

### 5.1 Décisions prises

| Date | Décision | Justification |
|------|----------|---------------|
| 2026-01-16 | PostgreSQL 16 | Multi-writer, JSONB, extensions |
| 2026-01-16 | Qdrant pour vecteurs | Open-source, auto-hébergé |
| 2026-01-16 | GPT-4o-mini pour traduction | Contexte OSINT, 100x moins cher que DeepL |
| 2026-01-16 | ARQ pour tâches de fond | Recommandé pour async Python |

### 5.2 Décisions en attente

| Sujet | Options | Deadline |
|-------|---------|----------|
| - | - | - |

---

## 6. Métriques

### 6.1 Métriques actuelles (Prototype)

| Métrique | Valeur |
|----------|--------|
| Messages collectés | N/A (à mesurer) |
| Canaux suivis | N/A (à mesurer) |
| Temps de traduction moyen | N/A (à mesurer) |
| Taux de déduplication | N/A (à mesurer) |

### 6.2 Objectifs M1

| Métrique | Objectif |
|----------|----------|
| Messages/jour | 10K+ |
| Canaux actifs | 50+ |
| Beta-testeurs | 10 |
| NPS | > 30 |

---

**Document mis à jour automatiquement après chaque fonctionnalité complétée.**
**Voir aussi:** [project_spec.md](./project_spec.md) | [architecture.md](./architecture.md) | [changelog.md](./changelog.md)
