# OSFeed Architecture Documentation

This directory contains architecture documentation for the OSFeed platform.

## Overview

OSFeed is a Telegram-first OSINT platform for collection, translation, deduplication, and daily digests. The system is built on a modern microservices architecture running entirely in Docker containers.

## Documentation

For detailed technical documentation:
- [Architecture Overview](./ARCHITECTURE.md) - System components, deployment, infrastructure, and key design decisions
- [Data Flow Guide](./DATA_FLOW.md) - Message processing pipeline and end-to-end data flows through all layers

## Architecture Diagrams

- [System Overview](./diagrams/system-overview.mmd) - High-level architecture showing all components and their interactions
- [Message Pipeline](./diagrams/message-pipeline.mmd) - Detailed message flow from collection to delivery

## Key Components

### Frontend
- **Technology**: React 18 + Vite + Tailwind CSS + Zustand + React Query
- **Features**: PWA support, command palette (⌘K), virtualized feeds, i18n (FR/EN)
- **Port**: 5173 (dev), 80 (production)

### Backend
- **Technology**: FastAPI (Python) + Uvicorn
- **Features**: REST API, WebSocket support, auth with JWT + refresh tokens, scheduler for background tasks
- **Port**: 8000

### Database Layer
- **PostgreSQL**: Primary data store for messages, channels, users, collections, and audit logs
- **Qdrant**: Vector database for semantic search and deduplication
- **Redis**: Cache layer for translations (persistent) and session data

### External Integrations
- **Telegram API**: Message collection with flood-wait handling
- **LLM APIs**: Translation with model routing (Gemini Flash default, GPT-4o-mini fallback)

### Infrastructure
- **Docker Compose**: Container orchestration for all services
- **Traefik**: Reverse proxy and SSL termination (production via Coolify)

## Data Flow

1. **Collection**: Backend collects messages from Telegram channels via Telegram API
2. **Processing**: Messages are translated (LLM), deduplicated (Qdrant vector embeddings)
3. **Storage**: Processed messages stored in PostgreSQL with metadata
4. **Caching**: Translation results cached in Redis for performance
5. **Presentation**: Frontend fetches data via REST API, displays with real-time updates

## Key Features

- **Collections**: Group channels, filter digests, scoped exports
- **Deduplication**: Vector similarity matching to identify duplicate content
- **Translation**: Multi-model routing with fallback (Gemini/GPT)
- **Daily Digests**: Automated HTML + PDF reports with key entities
- **Semantic Search**: Full-text + vector similarity search
- **Audit Logging**: RGPD-compliant audit trail for sensitive actions
- **API Usage Tracking**: LLM cost monitoring and analytics
- **Collection Sharing**: Viewer/editor/admin permissions

## Development

See the [main README](../README.md) for quickstart instructions.

All services run in Docker with hot-reloading enabled via volume mounts.

## Deployment

OSFeed is production-ready and deployed via Coolify with:
- Traefik reverse proxy for SSL termination
- Let's Encrypt certificates
- Health checks and auto-restart policies
- Resource limits (CPU/memory)

## Security

- JWT access tokens + refresh token rotation
- Password hashing with bcrypt
- API rate limiting
- CORS configuration
- Audit logging for compliance
- Environment-based secrets management

## Documentation Updates

When adding new architecture documentation:
1. Create diagrams in `./diagrams/` using Mermaid format (`.mmd` extension)
2. Add references to this README
3. Keep diagrams up-to-date with system changes
