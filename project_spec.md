# TeleScope - Project Specification Document
## Renseignement Opérationnel pour Telegram

**Version:** 1.0
**Date:** 2026-01-16 18:40
**Statut:** Phase 1 - Build M1

---

## Table des Matières

1. [Résumé Exécutif](#1-résumé-exécutif)
2. [Product Requirements](#2-product-requirements)
3. [Engineering Design](#3-engineering-design)
4. [Milestones](#4-milestones)
5. [Risques & Mitigations](#5-risques--mitigations)
6. [Annexes](#6-annexes)

---

## 1. Résumé Exécutif

### Vision
Transformer TeleScope d'un prototype personnel en une plateforme de **renseignement opérationnel** capable de filtrer le bruit de Telegram pour des clients institutionnels (journalistes d'investigation, analystes géopolitiques, services de défense).

### Proposition de Valeur
> "Du chaos informationnel à l'intelligence actionnable en 24h"

TeleScope résout le problème fondamental des professionnels de l'OSINT : **la surcharge cognitive** face aux milliers de messages quotidiens sur Telegram, dans des langues qu'ils ne maîtrisent pas, mélangés de propagande et de duplicatas.

### Décisions Stratégiques (validées)
| Décision | Choix | Justification |
|----------|-------|---------------|
| Modèle de déploiement | **Cloud SaaS** (MVP) → Hybride (v2) | Time-to-market rapide, option on-premise différée |
| Focus MVP | **Daily Digests & Analyse** | Valeur immédiate, différenciation vs agrégateurs |
| Niveau de sécurité | **Renforcé (RGPD + Audit)** | Requis pour médias EU et clients institutionnels |

---

## 2. Product Requirements

### 2.1 Utilisateurs Cibles

#### Persona 1 : Journaliste d'Investigation
| Attribut | Description |
|----------|-------------|
| **Profil** | Journaliste senior dans un média international (AFP, Le Monde, Bellingcat) |
| **Objectif** | Suivre l'évolution d'un conflit/crise via sources Telegram en temps quasi-réel |
| **Frustrations** | • Barrière de la langue (russe, arabe, ukrainien) <br> • Impossible de suivre 50+ canaux manuellement <br> • Difficulté à distinguer info vérifiée vs propagande |
| **Budget** | 200-500€/mois (budget outil individuel ou équipe) |
| **Métrique de succès** | Temps économisé : de 4h/jour à 30min pour le briefing matinal |

#### Persona 2 : Analyste Géopolitique / Défense
| Attribut | Description |
|----------|-------------|
| **Profil** | Analyste dans un think tank, ministère, ou entreprise de défense |
| **Objectif** | Produire des rapports de situation basés sur OSINT Telegram |
| **Frustrations** | • Manque de traçabilité des sources <br> • Duplicatas entre canaux pro-Kremlin <br> • Pas de vue consolidée multi-canaux |
| **Budget** | 1000-5000€/mois (licence entreprise/gouvernementale) |
| **Métrique de succès** | Couverture : passer de 10 canaux suivis manuellement à 100+ automatisés |

#### Persona 3 : Responsable Veille (Entreprise)
| Attribut | Description |
|----------|-------------|
| **Profil** | Directeur sûreté, risk manager, ou responsable intelligence économique |
| **Objectif** | Détecter les menaces réputationnelles ou sécuritaires concernant l'entreprise |
| **Frustrations** | • Telegram = angle mort de la veille traditionnelle <br> • Outils existants trop techniques <br> • Besoin de rapports exécutifs, pas de flux brut |
| **Budget** | 2000-10000€/mois |
| **Métrique de succès** | Alertes pertinentes : <10 par jour, 0 faux négatifs critiques |

### 2.2 Problèmes Résolus

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PROBLÈMES UTILISATEURS                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐      │
│  │ SURCHARGE        │  │ BARRIÈRE DE      │  │ POLLUTION        │      │
│  │ COGNITIVE        │  │ LA LANGUE        │  │ INFORMATIONNELLE │      │
│  │                  │  │                  │  │                  │      │
│  │ • 1000+ msg/jour │  │ • 70% contenu    │  │ • 40% duplicatas │      │
│  │ • 50+ canaux     │  │   non-anglais    │  │   cross-canal    │      │
│  │ • 0 priorisation │  │ • Traduction     │  │ • Propagande     │      │
│  │                  │  │   Google = bruit │  │   coordonnée     │      │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘      │
│           │                     │                     │                 │
│           └─────────────────────┼─────────────────────┘                 │
│                                 ▼                                       │
│                    ┌─────────────────────────┐                         │
│                    │  CONSÉQUENCE            │                         │
│                    │  Information critique   │                         │
│                    │  manquée ou retardée    │                         │
│                    └─────────────────────────┘                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### P1 : Surcharge Cognitive
- **Symptôme** : Un analyste passe 4h/jour à scroller Telegram sans méthodologie
- **Cause racine** : Absence de curation/priorisation automatisée
- **Solution TeleScope** : Daily Digests LLM avec résumés par thème/région

#### P2 : Barrière de la Langue
- **Symptôme** : Google Translate produit des traductions mot-à-mot incompréhensibles (jargon militaire, slang)
- **Cause racine** : Traducteurs génériques sans contexte OSINT
- **Solution TeleScope** : Traduction contextuelle LLM avec glossaire spécialisé (terminologie militaire, géopolitique)

#### P3 : Pollution Informationnelle
- **Symptôme** : Le même message relayé sur 20 canaux pro-Kremlin noie les infos originales
- **Cause racine** : Absence de déduplication cross-canal
- **Solution TeleScope** : Déduplication sémantique vectorielle + scoring d'originalité

### 2.3 Fonctionnalités Prioritaires (MVP)

#### F1 : Traduction Contextuelle LLM
| Attribut | Spécification |
|----------|---------------|
| **Description** | Traduction via GPT-4o-mini avec prompt spécialisé OSINT |
| **Input** | Message original + langue source détectée + contexte (canal, date) |
| **Output** | Traduction FR/EN + annotations (termes techniques, noms propres) |
| **Coût cible** | ~0.001$ par message (100x moins cher que DeepL API) |
| **Langues prioritaires** | Russe, Ukrainien, Arabe, Farsi, Chinois |

**Prompt de traduction (exemple) :**
```
Tu es un traducteur spécialisé OSINT/géopolitique. Traduis ce message Telegram
de {source_lang} vers {target_lang}.

Contexte : Canal "{channel_name}" - {channel_description}

Règles :
1. Préserve le ton et le style (formel/informel)
2. Annote les termes militaires entre [crochets]
3. Translittère les noms propres + traduction si pertinent
4. Signale les éléments de propagande évidents avec ⚠️

Message : {original_text}
```

#### F2 : Déduplication Sémantique Vectorielle
| Attribut | Spécification |
|----------|---------------|
| **Description** | Identification des messages similaires via embeddings vectoriels |
| **Algorithme** | 1. Embedding via text-embedding-3-small <br> 2. Recherche de similarité cosinus > 0.85 <br> 3. Clustering des duplicatas |
| **Output** | Score d'originalité (0-100), groupe de duplicatas, source primaire |
| **Performance cible** | O(log n) via index vectoriel vs O(n²) actuel |
| **Stockage** | Base vectorielle (Qdrant) + métadonnées PostgreSQL |

```
┌─────────────────────────────────────────────────────────────────────────┐
│                 DÉDUPLICATION SÉMANTIQUE                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Message A (Canal 1, 10:00)              Message B (Canal 2, 10:15)    │
│  "Войска РФ отступили из Херсона"        "Российские войска покинули   │
│                                           Херсонскую область"          │
│           │                                         │                  │
│           ▼                                         ▼                  │
│     ┌───────────┐                            ┌───────────┐             │
│     │ Embedding │                            │ Embedding │             │
│     │ [0.2, 0.8,│                            │ [0.19, 0.81│            │
│     │  0.1, ...] │                            │  0.12, ...]│            │
│     └─────┬─────┘                            └─────┬─────┘             │
│           │                                         │                  │
│           └──────────────┬──────────────────────────┘                  │
│                          ▼                                             │
│                  Similarité Cosinus = 0.94                             │
│                          ▼                                             │
│                 ┌─────────────────┐                                    │
│                 │ DUPLICATA       │                                    │
│                 │ Source: Canal 1 │                                    │
│                 │ Score: 94%      │                                    │
│                 └─────────────────┘                                    │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

#### F3 : Daily Digests Intelligents
| Attribut | Spécification |
|----------|---------------|
| **Description** | Résumé quotidien structuré des événements clés |
| **Format** | Markdown avec sections thématiques (Conflit, Politique, Économie) |
| **Contenu** | • Top 10 événements du jour <br> • Sources primaires citées <br> • Tendances émergentes <br> • Entités clés mentionnées |
| **Personnalisation** | Filtres par région, thème, canaux suivis |
| **Livraison** | Dashboard + Email (optionnel) |

**Structure du digest :**
```markdown
# Daily Digest - 16 Janvier 2026

## 🔥 Événements Majeurs
1. **[CONFLIT]** Offensive ukrainienne dans la région de Zaporizhzhia
   - Sources : @rybar (14:32), @militarysummary (15:10)
   - Originalité : 87% (confirmé par 3 sources indépendantes)

2. **[POLITIQUE]** Déclaration du Kremlin sur les négociations
   - Source primaire : @rian_ru (09:00)
   - Propagation : 23 canaux en 2h

## 📊 Statistiques
- Messages analysés : 2,847
- Duplicatas filtrés : 1,203 (42%)
- Langues : RU (68%), UA (22%), EN (10%)

## 🏷️ Entités Clés
- Personnes : Zelensky (89 mentions), Poutine (67), Shoigu (34)
- Lieux : Kherson (156), Zaporizhzhia (98), Bakhmut (87)
- Organisations : Wagner (45), NATO (34)
```

#### F4 : Gestion des Canaux & Collections
| Attribut | Spécification |
|----------|---------------|
| **Description** | Organisation des canaux en collections thématiques |
| **Fonctionnalités** | • Ajout par username ou lien t.me <br> • Métadonnées auto (abonnés, langue, description) <br> • Tags personnalisés <br> • Collections (ex: "Ukraine", "Proche-Orient") |
| **Import** | CSV, liste de liens, partage de collections entre utilisateurs |

#### F5 : Interface Utilisateur Repensée
| Attribut | Spécification |
|----------|---------------|
| **Dashboard** | Vue exécutive : KPIs, dernier digest, alertes |
| **Feed** | Timeline chronologique avec filtres avancés |
| **Recherche** | Full-text + sémantique (trouver des messages "similaires à...") |
| **Export** | PDF, CSV, JSON pour rapports |

### 2.4 Fonctionnalités Hors-Scope MVP

| Fonctionnalité | Milestone | Justification |
|----------------|-----------|---------------|
| Alerting temps réel (push) | M2 | Nécessite WebSockets, infrastructure temps réel |
| Analyse de sentiment avancée | M3 | Requiert fine-tuning de modèles |
| Détection de bots/coordination | M3 | Complexité algorithmique |
| Application mobile | M3+ | Focus desktop pour analystes |
| API publique | M2 | Priorité aux fonctionnalités core |
| Déploiement on-premise | M2 | Packaging et support dédié requis |

---

## 3. Engineering Design

### 3.1 Limitations de l'Architecture Actuelle

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ARCHITECTURE ACTUELLE (Pré-MVP)                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐    │
│    │ Telegram │────▶│ Telethon │────▶│ SQLite   │◀────│ FastAPI  │    │
│    │ Channels │     │ (1 lock) │     │ (1 file) │     │          │    │
│    └──────────┘     └──────────┘     └──────────┘     └──────────┘    │
│                           │                                  ▲         │
│                           ▼                                  │         │
│                     ┌──────────┐                       ┌──────────┐    │
│                     │ Google   │                       │ React    │    │
│                     │ Translate│                       │ Frontend │    │
│                     └──────────┘                       └──────────┘    │
│                                                                         │
│    LIMITATIONS:                                                         │
│    ❌ SQLite = single-writer, pas de scaling horizontal                │
│    ❌ Telethon lock global = collecte sérialisée                       │
│    ❌ Déduplication O(n²) = lenteur à 10K+ messages                    │
│    ❌ Google Translate = instable, pas de contexte                     │
│    ❌ Pas d'auth = données accessibles à tous                          │
│    ❌ Pas de logs d'audit = non conforme RGPD                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Architecture Cible (MVP)

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
│  │              │ (Bull/BullMQ) │                                           │    │
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
│  │ │LLM     │    │Embedding   │    │Entity    │                             │    │
│  │ │Transl. │    │Generation  │    │Extraction│                             │    │
│  │ │GPT-4o  │    │text-embed  │    │(NER)     │                             │    │
│  │ │-mini   │    │-3-small    │    │          │                             │    │
│  │ └───┬────┘    └─────┬──────┘    └────┬─────┘                             │    │
│  │     │               │                │                                    │    │
│  └─────┼───────────────┼────────────────┼────────────────────────────────────┘    │
│        │               │                │                                        │
│  ┌─────┼───────────────┼────────────────┼────────────────────────────────────┐    │
│  │     ▼               ▼                ▼         COUCHE STOCKAGE            │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                   PostgreSQL                          │                  │    │
│  │ │  • Messages (texte, métadonnées)                     │                  │    │
│  │ │  • Channels                                          │                  │    │
│  │ │  • Users & Auth                                      │                  │    │
│  │ │  • Audit Logs (RGPD)                                 │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  │                                                                           │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                       Qdrant                          │                  │    │
│  │ │  • Embeddings vectoriels (déduplication)             │                  │    │
│  │ │  • Index de recherche sémantique                     │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  │                                                                           │    │
│  │ ┌──────────────────────────────────────────────────────┐                  │    │
│  │ │                      Redis                            │                  │    │
│  │ │  • Cache traductions                                 │                  │    │
│  │ │  • Session store                                     │                  │    │
│  │ │  • Rate limiting                                     │                  │    │
│  │ └──────────────────────────────────────────────────────┘                  │    │
│  └───────────────────────────────────────────────────────────────────────────┘    │
│                                                                                   │
│  ┌───────────────────────────────────────────────────────────────────────────┐    │
│  │                         COUCHE API                                         │    │
│  │                                                                            │    │
│  │   ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │    │
│  │   │   FastAPI    │    │   Auth       │    │   Rate       │                │    │
│  │   │   REST API   │◀──▶│   (JWT)      │◀──▶│   Limiter    │                │    │
│  │   └──────┬───────┘    └──────────────┘    └──────────────┘                │    │
│  │          │                                                                 │    │
│  └──────────┼─────────────────────────────────────────────────────────────────┘    │
│             │                                                                      │
│  ┌──────────┼─────────────────────────────────────────────────────────────────┐    │
│  │          ▼                   COUCHE PRÉSENTATION                           │    │
│  │   ┌──────────────────────────────────────────────────────────────────┐    │    │
│  │   │                     React SPA (Vite + TailwindCSS)                │    │    │
│  │   │  • Dashboard avec KPIs                                           │    │    │
│  │   │  • Feed messages avec filtres                                    │    │    │
│  │   │  • Gestion canaux & collections                                  │    │    │
│  │   │  • Daily Digests                                                 │    │    │
│  │   │  • Export (PDF, CSV)                                             │    │    │
│  │   └──────────────────────────────────────────────────────────────────┘    │    │
│  └────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                    │
└────────────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Stack Technique Cible

#### Backend
| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Framework API | **FastAPI** (conservé) | Performant, async, bien maîtrisé |
| Base relationnelle | **PostgreSQL 16** | Multi-writer, JSONB, extensions |
| Base vectorielle | **Qdrant** | Open-source, auto-hébergé |
| Cache/Queue | **Redis 7** | Cache, sessions, rate limiting, queues |
| Task Queue | **Celery** ou **ARQ** | Jobs distribués, retry, monitoring |
| Auth | **FastAPI-Users** + JWT | OAuth2, sessions, RBAC |
| Logging | **Structlog** + **Sentry** | Logs structurés, error tracking |

#### LLM / IA
| Composant | Technologie | Coût estimé |
|-----------|-------------|-------------|
| Traduction | **GPT-4o-mini** via OpenAI | ~$0.00015/1K tokens input |
| Embeddings | **text-embedding-3-small** | ~$0.00002/1K tokens |
| Summarization | **GPT-4o-mini** | ~$0.0006/1K tokens output |
| NER (optionnel) | **spaCy** local | Gratuit |

**Comparaison coûts traduction :**
| Service | Coût / 1M caractères | Ratio |
|---------|---------------------|-------|
| DeepL API | $20 | 100x |
| Google Cloud Translation | $20 | 100x |
| **GPT-4o-mini** | **$0.15-0.30** | **1x** |

#### Frontend
| Composant | Technologie | Justification |
|-----------|-------------|---------------|
| Framework | **React 18** (conservé) | Écosystème mature |
| Build | **Vite** (conservé) | Fast HMR, ESM |
| State | **TanStack Query** (conservé) | Cache serveur optimisé |
| UI | **Tailwind CSS** + **shadcn/ui** | Composants accessibles |
| Charts | **Recharts** ou **Chart.js** | Visualisations KPIs |

#### Infrastructure (Cloud)
| Composant | Service | Tier MVP |
|-----------|---------|----------|
| Compute | **Railway** ou **Render** | ~$20/mois |
| PostgreSQL | **Neon** ou **Supabase** | Gratuit → $25/mois |
| Redis | **Upstash** | Gratuit jusqu'à 10K commands/jour |
| Vectoriel | **Qdrant** | Auto-hébergé (VPS) |
| Storage | **Cloudflare R2** | Gratuit 10GB |

**Coût infrastructure MVP estimé : $50-100/mois**

### 3.4 Schéma de Base de Données (PostgreSQL)

```sql
-- Extension pour UUID et recherche full-text
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Table utilisateurs (RGPD compliant)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user', -- 'admin', 'user', 'viewer'
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    -- RGPD
    consent_given_at TIMESTAMPTZ,
    data_retention_days INTEGER DEFAULT 365
);

-- Audit logs (RGPD compliance)
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL, -- 'login', 'view_message', 'export_data', etc.
    resource_type VARCHAR(50), -- 'message', 'channel', 'digest'
    resource_id UUID,
    ip_address INET,
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_logs_user ON audit_logs(user_id, created_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs(action, created_at DESC);

-- Canaux Telegram
CREATE TABLE channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    detected_language VARCHAR(10),
    subscriber_count INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_fetched_at TIMESTAMPTZ,
    fetch_config JSONB DEFAULT '{"frequency_minutes": 5, "max_messages": 100}'
);
CREATE INDEX idx_channels_username ON channels(username);
CREATE INDEX idx_channels_active ON channels(is_active) WHERE is_active = true;

-- Collections de canaux
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_shared BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE collection_channels (
    collection_id UUID REFERENCES collections(id) ON DELETE CASCADE,
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    PRIMARY KEY (collection_id, channel_id)
);

-- Messages
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    channel_id UUID REFERENCES channels(id) ON DELETE CASCADE,
    telegram_message_id BIGINT NOT NULL,

    -- Contenu
    original_text TEXT,
    translated_text TEXT,
    source_language VARCHAR(10),
    target_language VARCHAR(10) DEFAULT 'fr',

    -- Média
    media_type VARCHAR(50), -- 'photo', 'video', 'document', 'audio'
    media_urls JSONB,

    -- Déduplication
    is_duplicate BOOLEAN DEFAULT false,
    originality_score SMALLINT, -- 0-100
    duplicate_group_id UUID,
    embedding_id VARCHAR(255), -- ID dans Qdrant

    -- NER
    entities JSONB, -- {"persons": [], "locations": [], "organizations": []}

    -- Timestamps
    published_at TIMESTAMPTZ NOT NULL,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    translated_at TIMESTAMPTZ,

    UNIQUE(channel_id, telegram_message_id)
);

CREATE INDEX idx_messages_channel_published ON messages(channel_id, published_at DESC);
CREATE INDEX idx_messages_published ON messages(published_at DESC);
CREATE INDEX idx_messages_duplicate_group ON messages(duplicate_group_id) WHERE duplicate_group_id IS NOT NULL;
CREATE INDEX idx_messages_entities ON messages USING GIN(entities);

-- Full-text search
ALTER TABLE messages ADD COLUMN search_vector tsvector
    GENERATED ALWAYS AS (
        setweight(to_tsvector('simple', coalesce(original_text, '')), 'A') ||
        setweight(to_tsvector('simple', coalesce(translated_text, '')), 'B')
    ) STORED;
CREATE INDEX idx_messages_search ON messages USING GIN(search_vector);

-- Digests quotidiens
CREATE TABLE digests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    digest_type VARCHAR(50) DEFAULT 'daily', -- 'daily', 'weekly', 'custom'

    -- Contenu
    title VARCHAR(255),
    content TEXT NOT NULL,
    content_html TEXT,

    -- Statistiques
    message_count INTEGER DEFAULT 0,
    channels_covered INTEGER DEFAULT 0,
    duplicates_filtered INTEGER DEFAULT 0,

    -- Période
    period_start TIMESTAMPTZ NOT NULL,
    period_end TIMESTAMPTZ NOT NULL,

    -- Config
    filters JSONB, -- {"collections": [], "languages": [], "keywords": []}

    generated_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_digests_user_type ON digests(user_id, digest_type, generated_at DESC);

-- Cache des traductions (pour éviter re-traduction)
CREATE TABLE translation_cache (
    hash VARCHAR(64) PRIMARY KEY, -- SHA256 du texte original
    source_language VARCHAR(10),
    target_language VARCHAR(10),
    translated_text TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    hits INTEGER DEFAULT 1
);
```

### 3.5 Gestion des Flood Waits Telegram

```python
# Nouveau service de collecte avec retry et backoff
import asyncio
from telethon import TelegramClient
from telethon.errors import FloodWaitError, SlowModeWaitError
import random

class TelegramCollectorV2:
    def __init__(self, client: TelegramClient):
        self.client = client
        self.base_delay = 1.0  # Délai de base entre requêtes
        self.max_retries = 3

    async def fetch_with_backoff(self, channel_id: int, limit: int = 100):
        """Fetch messages avec exponential backoff."""
        for attempt in range(self.max_retries):
            try:
                # Ajouter jitter pour éviter thundering herd
                jitter = random.uniform(0.5, 1.5)
                await asyncio.sleep(self.base_delay * jitter)

                messages = await self.client.get_messages(
                    channel_id,
                    limit=limit
                )
                return messages

            except FloodWaitError as e:
                wait_time = e.seconds + random.uniform(1, 5)
                logger.warning(f"Flood wait: sleeping {wait_time}s")
                await asyncio.sleep(wait_time)

            except SlowModeWaitError as e:
                await asyncio.sleep(e.seconds)

        raise Exception(f"Failed after {self.max_retries} retries")

    async def collect_all_channels(self, channels: list):
        """Collecte distribuée avec rate limiting global."""
        semaphore = asyncio.Semaphore(3)  # Max 3 canaux en parallèle

        async def fetch_channel(channel):
            async with semaphore:
                return await self.fetch_with_backoff(channel.telegram_id)

        tasks = [fetch_channel(ch) for ch in channels]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

### 3.6 Pipeline de Traitement

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
│                         │ LLM           │         │ (TTL 7 jours) │    │
│                         │               │         │               │    │
│                         └───────┬───────┘         └───────────────┘    │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐         ┌───────────────┐    │
│                         │               │         │               │    │
│                         │ Embedding     │────────▶│ Qdrant        │    │
│                         │ Génération    │         │ (vecteurs)    │    │
│                         │               │         │               │    │
│                         └───────┬───────┘         └───────────────┘    │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐                              │
│                         │               │                              │
│                         │ Déduplication │                              │
│                         │ Sémantique    │                              │
│                         │               │                              │
│                         └───────┬───────┘                              │
│                                 │                                       │
│                                 ▼                                       │
│                         ┌───────────────┐                              │
│                         │               │                              │
│                         │ NER           │                              │
│                         │ (Entités)     │                              │
│                         │               │                              │
│                         └───────────────┘                              │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.7 Sécurité & Conformité RGPD

#### Authentification & Autorisation
```python
# Modèle RBAC (Role-Based Access Control)
ROLES = {
    "admin": ["*"],  # Tous les droits
    "analyst": [
        "channels:read", "channels:create",
        "messages:read", "messages:search",
        "digests:read", "digests:create",
        "export:csv", "export:pdf"
    ],
    "viewer": [
        "messages:read",
        "digests:read"
    ]
}
```

#### Audit Logging
```python
# Middleware d'audit automatique
async def audit_middleware(request: Request, call_next):
    response = await call_next(request)

    if request.user and request.method in ["POST", "PUT", "DELETE", "GET"]:
        await audit_log.create(
            user_id=request.user.id,
            action=f"{request.method}:{request.url.path}",
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            metadata={
                "status_code": response.status_code,
                "query_params": dict(request.query_params)
            }
        )

    return response
```

#### Conformité RGPD
| Exigence | Implémentation |
|----------|----------------|
| Consentement | Checkbox obligatoire à l'inscription |
| Droit d'accès | Endpoint `/api/me/data` (export JSON) |
| Droit à l'oubli | Endpoint `/api/me/delete` (anonymisation) |
| Portabilité | Export JSON/CSV de toutes les données utilisateur |
| Logs d'audit | Table `audit_logs` avec rétention 2 ans |
| Chiffrement | TLS en transit, chiffrement at-rest (PostgreSQL) |
| Minimisation | Pas de collecte de données non nécessaires |

---

## 4. Milestones

### 4.1 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              ROADMAP PRODUIT                                     │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│  MILESTONE 1                MILESTONE 2                MILESTONE 3               │
│  MVP de Niche              Alerting Pro               Intelligence              │
│                                                        Avancée                  │
│  ┌─────────────┐           ┌─────────────┐            ┌─────────────┐           │
│  │             │           │             │            │             │           │
│  │ • Traduction│           │ • Alertes   │            │ • Sentiment │           │
│  │   LLM       │           │   temps réel│            │   analysis  │           │
│  │             │           │             │            │             │           │
│  │ • Dédupli-  │           │ • API       │            │ • Détection │           │
│  │   cation    │           │   publique  │            │   bots      │           │
│  │   sémantique│           │             │            │             │           │
│  │             │           │ • Webhooks  │            │ • Graphes   │           │
│  │ • Daily     │           │             │            │   de        │           │
│  │   Digests   │           │ • On-premise│            │   propagation│          │
│  │             │           │   option    │            │             │           │
│  │ • Auth &    │           │             │            │ • Mobile    │           │
│  │   RGPD      │           │ • Multi-    │            │   app       │           │
│  │             │           │   tenant    │            │             │           │
│  └─────────────┘           └─────────────┘            └─────────────┘           │
│                                                                                  │
│  Cible: Journalistes       Cible: +Défense            Cible: Enterprise        │
│         Freelances                Think tanks                                   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Milestone 1 : MVP de Niche

**Objectif** : Produit utilisable par des journalistes d'investigation et analystes indépendants.

**Critères de succès** :
- [ ] 10 beta-testeurs actifs (journalistes/analystes)
- [ ] 50 canaux monitorés simultanément
- [ ] 10K+ messages traités par jour
- [ ] NPS > 30

#### Fonctionnalités incluses

| Feature | Priorité | Complexité | Description |
|---------|----------|------------|-------------|
| Migration PostgreSQL | P0 | Moyenne | Remplacer SQLite, schéma v2 |
| Authentification JWT | P0 | Moyenne | Login/register, sessions |
| Traduction LLM | P0 | Haute | GPT-4o-mini avec prompt OSINT |
| Base vectorielle | P0 | Haute | Qdrant, embeddings, dédup |
| Daily Digests v2 | P1 | Moyenne | Structurés par thème/région |
| Collections de canaux | P1 | Basse | Groupes thématiques |
| Dashboard KPIs | P1 | Basse | Stats, tendances |
| Export CSV/PDF | P2 | Basse | Rapports téléchargeables |
| Audit logs RGPD | P2 | Moyenne | Conformité |
| Flood Wait handling | P0 | Moyenne | Backoff exponentiel |

#### Livrables techniques

```
telescope/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── v1/
│   │   │   │   ├── auth.py          # JWT login/register
│   │   │   │   ├── channels.py      # CRUD canaux
│   │   │   │   ├── collections.py   # Gestion collections
│   │   │   │   ├── messages.py      # Feed + search
│   │   │   │   ├── digests.py       # Daily digests
│   │   │   │   └── export.py        # CSV/PDF
│   │   │   └── deps.py              # Dependencies (auth, db)
│   │   ├── core/
│   │   │   ├── config.py            # Settings
│   │   │   ├── security.py          # JWT, hashing
│   │   │   └── logging.py           # Structlog config
│   │   ├── models/                  # SQLAlchemy models (PostgreSQL)
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── services/
│   │   │   ├── telegram/
│   │   │   │   ├── collector.py     # Avec backoff
│   │   │   │   └── session.py       # Multi-session manager
│   │   │   ├── llm/
│   │   │   │   ├── translator.py    # GPT-4o-mini
│   │   │   │   ├── summarizer.py    # Digest generation
│   │   │   │   └── prompts.py       # Prompt templates
│   │   │   ├── vector/
│   │   │   │   ├── embedder.py      # text-embedding-3-small
│   │   │   │   └── deduplicator.py  # Qdrant search
│   │   │   └── audit.py             # RGPD logging
│   │   ├── jobs/
│   │   │   ├── collector_job.py
│   │   │   └── digest_job.py
│   │   └── main.py
│   ├── alembic/                     # Migrations DB
│   ├── scripts/                     # Scripts utilitaires (migration, checks)
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                     # Providers + router
│   │   ├── components/              # UI + layout + domain
│   │   ├── features/                # Pages par feature
│   │   ├── hooks/                   # Custom hooks
│   │   ├── lib/                     # Utils, API client
│   │   ├── stores/                  # Zustand stores
│   │   └── styles/                  # Global styles
│   ├── components.json              # shadcn/ui config
│   └── package.json
├── docker-compose.yml               # PostgreSQL, Redis, Qdrant
├── .env.example
└── README.md
```

### 4.3 Milestone 2 : Alerting Pro

**Objectif** : Notifications temps réel et API pour intégrations.

**Nouvelles fonctionnalités** :
| Feature | Description |
|---------|-------------|
| Alertes temps réel | Push sur mots-clés, entités, seuils |
| WebSockets | Live feed sans polling |
| API publique | REST + SDK Python/JS |
| Webhooks | Intégration Slack, Teams, Discord |
| Multi-tenant | Isolation par organisation |
| On-premise option | Docker Compose autonome |

### 4.4 Milestone 3 : Intelligence Avancée

**Objectif** : Analyse avancée pour entreprises et gouvernements.

**Nouvelles fonctionnalités** :
| Feature | Description |
|---------|-------------|
| Sentiment analysis | Classification pro/anti/neutre |
| Détection de bots | Scoring d'authenticité |
| Graphes de propagation | Visualisation des réseaux d'influence |
| Fine-tuned models | Modèles spécialisés par domaine |
| Application mobile | iOS/Android pour alertes |
| SSO enterprise | SAML, OIDC |

---

## 5. Risques & Mitigations

| Risque | Probabilité | Impact | Mitigation |
|--------|-------------|--------|------------|
| **Ban compte Telegram** | Haute | Critique | Multi-comptes, proxy rotation, rate limiting strict |
| **Coûts LLM explosent** | Moyenne | Haute | Monitoring usage, cache agressif, fallback modèles locaux |
| **Coût/ops Qdrant** | Moyenne | Moyenne | Scaling vertical + monitoring VPS |
| **Changement API Telegram** | Basse | Haute | Abstraction layer, monitoring changelog |
| **Concurrence (Palantir, etc.)** | Haute | Moyenne | Niche (Telegram-first), prix accessible |
| **Complexité RGPD** | Moyenne | Moyenne | DPO consultant, privacy by design |

---

## 6. Annexes

### 6.1 Glossaire

| Terme | Définition |
|-------|------------|
| **OSINT** | Open Source Intelligence - renseignement en sources ouvertes |
| **Embedding** | Représentation vectorielle d'un texte pour comparaison sémantique |
| **Flood Wait** | Limitation de débit imposée par Telegram |
| **NER** | Named Entity Recognition - extraction d'entités nommées |
| **Digest** | Résumé consolidé de messages sur une période |

### 6.2 Références

- [Telegram API Documentation](https://core.telegram.org/api)
- [Telethon Documentation](https://docs.telethon.dev/)
- [OpenAI API Pricing](https://openai.com/pricing)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [RGPD - CNIL](https://www.cnil.fr/fr/rgpd-de-quoi-parle-t-on)

### 6.3 Contacts

| Rôle | Responsabilité |
|------|----------------|
| Product Owner | Définition des priorités, validation UX |
| Tech Lead | Architecture, choix techniques |
| DevOps | Infrastructure, CI/CD |

---

**Document rédigé le 16 Janvier 2026**
**Prochaine révision : Post-validation MVP**
