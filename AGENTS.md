# OSFeed - Agentic Coding Guidelines

This document provides context and guidelines for AI agents working on the OSFeed codebase.

## 1. Project Overview
OSFeed is a Telegram-first OSINT platform for collection, translation, deduplication, and daily digests.
- **Backend**: Python (FastAPI, SQLAlchemy Async, Celery/APScheduler)
- **Frontend**: TypeScript (React 18, Vite, Tailwind, Zustand, React Query)
- **Database**: PostgreSQL (Data), Qdrant (Vector), Redis (Cache)

## 2. Environment & Commands

### Backend (`/backend`)
*   **Run Dev Server**: `uvicorn app.main:app --reload` (Port 8000)
*   **Run Tests**:
    *   All tests: `pytest`
    *   Single test: `pytest tests/path/to/test.py -k test_function_name`
    *   Specific file: `pytest tests/path/to/test.py`
*   **Migrations**:
    *   Create: `alembic revision --autogenerate -m "message"`
    *   Apply: `alembic upgrade head`

### Frontend (`/frontend`)
*   **Run Dev Server**: `npm run dev` (Port 5173)
*   **Build**: `npm run build` (Type check + Vite build)
*   **Preview**: `npm run preview`
*   **Test (E2E)**:
    *   Run all: `npm run test:e2e`
    *   Run UI mode: `npx playwright test --ui`

## 3. Code Structure

### Backend
*   `app/api/`: API Routers (keep logic thin, delegate to services)
*   `app/services/`: Business logic (Translation, Collection, Deduplication)
*   `app/models/`: SQLAlchemy ORM models
*   `app/schemas/`: Pydantic schemas (Request/Response validation)
*   `app/jobs/`: Background tasks (APScheduler)

### Frontend
*   `src/features/`: Feature-based modules (Auth, Channels, Messages) containing pages and components
*   `src/components/ui/`: Reusable UI primitives (Shadcn-like)
*   `src/lib/`: Utilities, API client
*   `src/stores/`: Zustand state management
*   `src/hooks/`: Custom React hooks

## 4. Code Style & Conventions

### General
*   **Type Safety**: STRICT usage of types. No `any` (TS) or untyped functions (Python).
*   **Async/Await**: Both Backend (FastAPI/AsyncPG) and Frontend (Promises) rely heavily on async patterns.

### Python (Backend)
*   **Type Hints**: Mandatory for function arguments and return values.
    *   `async def get_items(limit: int = 10) -> list[Item]:`
*   **Pydantic**: Use Pydantic models for all data exchange schemas.
*   **SQLAlchemy**: Use async session (`AsyncSession`). avoid sync DB calls.
*   **Error Handling**: Use `HTTPException` in routers.
*   **Naming**: `snake_case` for variables/functions, `PascalCase` for Classes/Models.

### TypeScript (Frontend)
*   **Components**: Functional components only.
    *   `export const MyComponent = ({ prop }: Props) => { ... }`
*   **Imports**: Use `@/` alias for local imports.
    *   `import { Button } from '@/components/ui/button'`
*   **Styling**: Tailwind CSS via `className` prop. Use `cn()` utility for conditional classes.
    *   `className={cn("base-class", condition && "active-class")}`
*   **State**: Use Zustand for global state, React Query for server state.
*   **Naming**: `camelCase` for variables/functions, `PascalCase` for Components/Types.
*   **Files**: `kebab-case` for filenames (e.g., `user-profile.tsx`).

## 5. Testing Guidelines
*   **Backend**: Focus on integration tests for API endpoints using `AsyncClient`. Mock external services (Telegram, OpenAI) where appropriate.
*   **Frontend**: Use Playwright for critical user flows (Login, Navigation, Export).
*   **Do not break existing tests.** Run tests before finalizing changes.

## 6. Git & Workflow
*   **Commits**: Conventional Commits (e.g., `feat: add export dialog`, `fix: resolve translation error`).
*   **Changes**: Keep changes atomic. Do not mix refactoring with feature work.
*   **Dependencies**: Check `package.json` or `requirements.txt` before adding new libraries. Prefer existing ones.

## 7. AI-Specific Notes
*   When editing backend, restart `uvicorn` if not in reload mode (usually is).
*   When editing frontend, Vite HMR handles updates.
*   **Secrets**: NEVER commit `.env` files or hardcode credentials.
*   **Documentation**: Update docstrings and README if architectural changes are made.

