# Contributing to OSFeed

Thank you for your interest in contributing to OSFeed! This guide will help you understand the architecture, navigate the codebase, and follow our development workflow.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Project Structure](#project-structure)
- [Development Workflow](#development-workflow)
- [How to Navigate the Codebase](#how-to-navigate-the-codebase)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Submitting Changes](#submitting-changes)

## Architecture Overview

OSFeed is a Telegram-first OSINT platform built with a modern, containerized architecture. The platform consists of:

- **Frontend**: React 18 with TypeScript, Vite, Tailwind CSS, Zustand, and React Query
- **Backend**: FastAPI with async SQLAlchemy, Pydantic v2, and APScheduler
- **Data Layer**: PostgreSQL (primary), Qdrant (vector search), Redis (caching)
- **External Integrations**: Telegram API (user sessions), LLM APIs (translation)

### Key Architectural Patterns

- **Service Layer Pattern**: Business logic isolated in service modules
- **Repository Pattern**: Database access abstracted through SQLAlchemy models
- **Event-Driven Processing**: Asynchronous message processing with queue-based orchestration
- **API-First Design**: RESTful API with WebSocket support for real-time updates

For detailed architecture documentation, see:
- [Architecture Overview](docs/ARCHITECTURE.md) - Comprehensive system design and components
- [Data Flow Guide](docs/DATA_FLOW.md) - Message processing pipeline and data flows

## Project Structure

OSFeed uses a monorepo structure with separate frontend and backend codebases:

```
OSFeed/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/               # API endpoints (REST routes)
│   │   ├── auth/              # Authentication & RBAC
│   │   ├── cli/               # CLI tools (Telegram setup)
│   │   ├── jobs/              # Background jobs (APScheduler)
│   │   ├── middleware/        # ASGI middleware (security headers)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   ├── schemas/           # Pydantic request/response models
│   │   ├── services/          # Business logic layer
│   │   ├── templates/         # Email templates (Jinja2)
│   │   ├── utils/             # Utilities (export, cache, retry)
│   │   ├── config.py          # Configuration management
│   │   ├── database.py        # Database session factory
│   │   └── main.py            # FastAPI app entry point
│   ├── alembic/               # Database migrations
│   ├── tests/                 # Backend tests (pytest)
│   ├── Dockerfile             # Backend container image
│   └── requirements.txt       # Python dependencies
│
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── app/              # App configuration (router, providers)
│   │   ├── components/       # Reusable UI components
│   │   │   ├── ui/          # shadcn/ui base components
│   │   │   ├── channels/    # Channel-specific components
│   │   │   ├── collections/ # Collection management UI
│   │   │   ├── common/      # Shared components (badges, timestamps)
│   │   │   ├── exports/     # Export dialogs
│   │   │   ├── layout/      # App shell, header, sidebar
│   │   │   ├── messages/    # Message feed, cards, filters
│   │   │   └── stats/       # Dashboard visualizations
│   │   ├── features/         # Feature modules (pages)
│   │   │   ├── auth/        # Login, register, password reset
│   │   │   ├── channels/    # Channel management
│   │   │   ├── collections/ # Collection views
│   │   │   ├── dashboard/   # KPI dashboard
│   │   │   ├── exports/     # Export history
│   │   │   ├── feed/        # Message feed
│   │   │   ├── landing/     # Landing page
│   │   │   ├── search/      # Full-text & semantic search
│   │   │   └── settings/    # User preferences
│   │   ├── hooks/            # Custom React hooks
│   │   ├── locales/          # i18n translations (FR/EN)
│   │   ├── stores/           # Zustand state management
│   │   ├── styles/           # Global CSS (Tailwind)
│   │   ├── types/            # TypeScript type definitions
│   │   └── main.tsx          # App entry point
│   ├── public/               # Static assets
│   ├── Dockerfile            # Frontend container image
│   ├── package.json          # npm dependencies
│   └── vite.config.ts        # Vite build configuration
│
├── docs/                      # Documentation
│   ├── ARCHITECTURE.md        # System architecture
│   ├── DATA_FLOW.md          # Data flow guide
│   └── diagrams/             # Mermaid diagrams
│
├── data/                      # Persistent data (gitignored)
│   ├── postgres/             # PostgreSQL data
│   ├── qdrant/               # Qdrant vector storage
│   └── redis/                # Redis persistence
│
├── .env.example              # Environment variables template
├── docker-compose.yml        # Full-stack orchestration
├── start.sh                  # Start script (migrations + services)
└── stop.sh                   # Stop all services
```

## Development Workflow

### 1. Initial Setup

Clone the repository and start the development environment:

```bash
git clone https://github.com/your-org/osfeed.git
cd osfeed
```

Copy the environment template and configure credentials:

```bash
cp .env.example .env
# Edit .env with your API keys and secrets
```

**Required Environment Variables:**
- `SECRET_KEY` - Application secret key (generate with `openssl rand -hex 32`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` - PostgreSQL credentials
- `TELEGRAM_API_ID`, `TELEGRAM_API_HASH` - Telegram API credentials (from my.telegram.org)
- `OPENAI_API_KEY` - OpenAI API key for LLM translation
- `REDIS_URL` - Redis connection string (optional, defaults to `redis://redis:6379`)

### 2. Start Development Environment

Start all services with hot-reloading enabled:

```bash
./start.sh
```

This script:
1. Starts Docker services (PostgreSQL, Qdrant, Redis, Backend, Frontend)
2. Waits for database readiness
3. Runs database migrations (`alembic upgrade head`)
4. Enables hot-reloading via volume mounts

**Access Points:**
- Frontend: http://localhost:5173 (Vite dev server with HMR)
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs (OpenAPI/Swagger)

### 3. Development Cycle

#### Backend Development

**Hot-reloading**: Uvicorn watches for file changes and automatically reloads.

**Common Tasks:**

```bash
# View backend logs
docker compose logs -f backend

# Run database migrations
docker compose exec backend alembic upgrade head

# Create a new migration
docker compose exec backend alembic revision --autogenerate -m "description"

# Run tests
docker compose exec backend pytest

# Run specific test
docker compose exec backend pytest tests/test_auth.py -v

# Access Python shell with app context
docker compose exec backend python
```

#### Frontend Development

**Hot-reloading**: Vite dev server provides instant HMR (Hot Module Replacement).

**Common Tasks:**

```bash
# View frontend logs
docker compose logs -f frontend

# Install new npm package
docker compose exec frontend npm install <package-name>

# Run type checking
docker compose exec frontend npm run type-check

# Build production bundle
docker compose exec frontend npm run build
```

### 4. Stop Services

```bash
./stop.sh
```

## How to Navigate the Codebase

### Finding API Endpoints

API routes are organized by resource in `backend/app/api/`:

```
backend/app/api/
├── auth.py          # Authentication (login, register, refresh)
├── channels.py      # Channel CRUD, stats, fetch jobs
├── collections.py   # Collection management, sharing, alerts
├── messages.py      # Message feed, search, translation, exports
├── alerts.py        # Alert configuration and history
├── audit_logs.py    # Audit log retrieval
└── stats.py         # Dashboard KPIs, API usage tracking
```

**Example**: To find the message feed endpoint, check `backend/app/api/messages.py`.

### Finding Business Logic

Service modules encapsulate business logic in `backend/app/services/`:

```
backend/app/services/
├── telegram_client.py              # Telegram API wrapper
├── llm_translator.py               # LLM translation (model routing)
├── translation_service.py          # Translation orchestration
├── message_search_service.py       # Full-text + semantic search
├── message_export_service.py       # CSV/PDF/HTML exports
├── cache_service.py                # Redis cache management
├── fetch_queue.py                  # Message collection queue
├── channel_join_queue.py           # Daily channel join queue
├── rate_limiter.py                 # Telegram API rate limiting
└── audit.py                        # Audit log creation
```

**Example**: Translation logic is in `llm_translator.py` (model selection) and `translation_service.py` (orchestration).

### Finding Database Models

SQLAlchemy ORM models are in `backend/app/models/`:

```
backend/app/models/
├── user.py              # User accounts, preferences
├── channel.py           # Telegram channels
├── message.py           # Messages + translations
├── collection.py        # Channel collections
├── collection_share.py  # Collection sharing permissions
├── alert.py             # Collection alerts
├── fetch_job.py         # Fetch job tracking
├── audit_log.py         # Audit logs (RGPD)
└── api_usage.py         # LLM API usage tracking
```

**Example**: To understand message storage, check `message.py` for the `Message` model.

### Finding Request/Response Schemas

Pydantic models for API validation are in `backend/app/schemas/`:

```
backend/app/schemas/
├── user.py              # UserCreate, UserResponse, UserUpdate
├── channel.py           # ChannelCreate, ChannelResponse
├── message.py           # MessageResponse, MessageFilters
├── collection.py        # CollectionCreate, CollectionResponse
└── stats.py             # KPIStats, APIUsageStats
```

**Example**: API request/response validation for channels is in `channel.py`.

### Finding Background Jobs

Scheduled jobs (APScheduler) are in `backend/app/jobs/`:

```
backend/app/jobs/
├── collect_messages.py           # Fetch messages from channels
├── translate_pending_messages.py # Batch translation job
├── alerts.py                     # Collection alert monitoring
└── purge_audit_logs.py           # RGPD audit log cleanup
```

**Example**: Message collection logic is in `collect_messages.py`.

### Finding Frontend Components

React components are organized by type in `frontend/src/components/`:

```
frontend/src/components/
├── ui/               # Base shadcn/ui components (button, card, dialog)
├── channels/         # Channel list, cards, dialogs
├── collections/      # Collection manager, stats, sharing
├── common/           # Shared utilities (badges, timestamps, error boundaries)
├── exports/          # Export dialogs
├── layout/           # App shell, header, sidebar, notifications
├── messages/         # Message feed, cards, filters, duplicates
└── stats/            # KPI cards, charts, rankings
```

**Example**: Message feed UI is in `components/messages/message-feed.tsx`.

### Finding Frontend Pages

Feature modules (pages) are in `frontend/src/features/`:

```
frontend/src/features/
├── auth/            # Login, register, password reset
├── channels/        # Channel management pages
├── collections/     # Collection detail and list pages
├── dashboard/       # KPI dashboard
├── exports/         # Export history page
├── feed/            # Main message feed
├── landing/         # Landing page
├── search/          # Full-text & semantic search
└── settings/        # User settings
```

**Example**: The main feed page is `features/feed/feed-page.tsx`.

### Finding State Management

Zustand stores are in `frontend/src/stores/`:

```
frontend/src/stores/
├── auth-store.ts          # User session, login state
├── collection-store.ts    # Active collection filter
├── notification-store.ts  # In-app notifications
└── settings-store.ts      # User preferences (language, theme)
```

**Example**: Authentication state is managed in `auth-store.ts`.

### Finding Database Migrations

Alembic migrations are versioned in `backend/alembic/versions/`:

- **Naming convention**: `<hash>_<description>.py`
- **Upgrade**: Apply schema changes
- **Downgrade**: Revert schema changes

**Example**: To see the initial schema, check `be3f078b6cf1_initial_schema_with_users_channels_.py`.

## Coding Standards

### Backend (Python)

- **Style**: Follow PEP 8 (use `black` for formatting)
- **Type Hints**: Use type annotations for function signatures
- **Async/Await**: Use async for I/O-bound operations (database, HTTP)
- **Dependency Injection**: Use FastAPI's dependency system for database sessions, auth
- **Error Handling**: Use custom exceptions, return appropriate HTTP status codes
- **Logging**: Use Python's `logging` module (not `print`)

**Example Service Function:**

```python
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.message import Message
from app.schemas.message import MessageResponse

async def get_message_by_id(
    db: AsyncSession,
    message_id: int,
    user_id: int
) -> MessageResponse:
    """Retrieve a single message by ID with access control."""
    result = await db.execute(
        select(Message).where(
            Message.id == message_id,
            Message.channel.has(Channel.user_id == user_id)
        )
    )
    message = result.scalar_one_or_none()
    if not message:
        raise HTTPException(status_code=404, detail="Message not found")
    return MessageResponse.from_orm(message)
```

### Frontend (TypeScript/React)

- **Style**: Follow Airbnb style guide (use ESLint + Prettier)
- **Components**: Use functional components with hooks
- **TypeScript**: Strict mode enabled, no `any` types
- **State Management**: Use Zustand for global state, React Query for server state
- **Styling**: Use Tailwind utility classes (avoid custom CSS)
- **Accessibility**: Use semantic HTML, ARIA labels where needed

**Example Component:**

```tsx
import { useQuery } from '@tanstack/react-query'
import { MessageCard } from '@/components/messages/message-card'
import { Message } from '@/types/message'

interface MessageFeedProps {
  channelId?: number
  collectionId?: number
}

export function MessageFeed({ channelId, collectionId }: MessageFeedProps) {
  const { data: messages, isLoading, error } = useQuery({
    queryKey: ['messages', { channelId, collectionId }],
    queryFn: () => fetchMessages({ channelId, collectionId }),
  })

  if (isLoading) return <MessageSkeleton />
  if (error) return <ErrorState error={error} />

  return (
    <div className="space-y-4">
      {messages?.map((message: Message) => (
        <MessageCard key={message.id} message={message} />
      ))}
    </div>
  )
}
```

## Testing Guidelines

### Backend Tests

Tests use pytest with async support (pytest-asyncio):

```bash
# Run all tests
docker compose exec backend pytest

# Run with coverage
docker compose exec backend pytest --cov=app --cov-report=html

# Run specific test file
docker compose exec backend pytest tests/test_auth.py -v

# Run tests matching pattern
docker compose exec backend pytest -k "test_login" -v
```

**Test Structure:**

```
backend/tests/
├── conftest.py              # Pytest fixtures (db session, test client)
├── test_auth.py            # Authentication tests
├── test_channels.py        # Channel CRUD tests
├── test_messages.py        # Message API tests
└── test_translation.py     # Translation service tests
```

**Example Test:**

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_channel(async_client: AsyncClient, auth_headers: dict):
    """Test channel creation endpoint."""
    response = await async_client.post(
        "/api/channels/",
        json={"name": "Test Channel", "url": "https://t.me/testchannel"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Channel"
    assert data["id"] is not None
```

### Frontend Tests

Tests use Vitest with React Testing Library:

```bash
# Run all tests
docker compose exec frontend npm test

# Run in watch mode
docker compose exec frontend npm test -- --watch

# Run with coverage
docker compose exec frontend npm run test:coverage
```

**Test Structure:**

```
frontend/src/__tests__/
├── auth.test.tsx           # Authentication flow tests
├── message-feed.test.tsx   # Message feed tests
└── collection-manager.test.tsx  # Collection management tests
```

## Submitting Changes

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow coding standards
- Add tests for new functionality
- Update documentation if needed

### 3. Run Tests

```bash
# Backend tests
docker compose exec backend pytest

# Frontend tests
docker compose exec frontend npm test
```

### 4. Commit Your Changes

Use conventional commit messages:

```bash
git add .
git commit -m "feat: add collection export to CSV"
git commit -m "fix: resolve duplicate message bug"
git commit -m "docs: update architecture diagram"
```

**Commit Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Test additions or updates
- `chore:` - Build process or tooling changes

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:
- **Title**: Clear, descriptive summary
- **Description**: What changed, why, and how to test
- **Screenshots**: For UI changes
- **Checklist**: Tests pass, documentation updated, no breaking changes

### 6. Code Review

- Address review feedback
- Keep commits clean (squash if needed)
- Ensure CI/CD passes

---

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue with reproduction steps
- **Security**: Email security@osfeed.example.com (do not open public issues)

Thank you for contributing to OSFeed! 🚀
