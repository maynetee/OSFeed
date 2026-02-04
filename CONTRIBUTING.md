# Contributing to OSFeed

Thank you for your interest in contributing to OSFeed! This document provides guidelines and best practices for contributing to the project.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Style](#code-style)
- [Testing](#testing)
- [Pull Request Process](#pull-request-process)
- [Architecture and Design](#architecture-and-design)
- [Common Tasks](#common-tasks)
- [Getting Help](#getting-help)

## Getting Started

### Prerequisites

OSFeed runs entirely in Docker, so you only need:
- **Docker** (version 20.10 or later)
- **Docker Compose** (version 2.0 or later)
- **Git** for version control

No local Python or Node.js installation is required!

### Initial Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/osfeed.git
   cd osfeed
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and configure at minimum:
   - `SECRET_KEY` - Generate a secure random string for JWT tokens
   - `POSTGRES_PASSWORD` - Set a strong database password
   - Optional but recommended: OpenAI API key, Telegram credentials, Redis settings

3. **Start the development environment:**
   ```bash
   docker compose up -d
   ```

   This will:
   - Start PostgreSQL, Redis, and Qdrant services
   - Build and launch the backend (FastAPI)
   - Build and launch the frontend (React + Vite)
   - Apply database migrations automatically

4. **Access the application:**
   - Frontend: http://localhost:5173 (with hot-reload)
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs (OpenAPI/Swagger)

5. **View logs:**
   ```bash
   # All services
   docker compose logs -f

   # Specific service
   docker compose logs -f backend
   docker compose logs -f frontend
   ```

6. **Stop the environment:**
   ```bash
   docker compose down
   ```

## Development Workflow

### Hot-Reload Development

Both frontend and backend support hot-reloading via volume mounts:

- **Frontend**: Vite dev server automatically reloads on file changes
- **Backend**: Uvicorn reloads on Python file changes

Simply edit files in your local `frontend/` or `backend/` directories and changes will be reflected immediately.

### Database Migrations

OSFeed uses Alembic for database schema migrations.

**Creating a new migration:**
```bash
docker compose exec backend alembic revision --autogenerate -m "Description of changes"
```

**Applying migrations:**
```bash
docker compose exec backend alembic upgrade head
```

**Rolling back:**
```bash
docker compose exec backend alembic downgrade -1
```

### Branch Strategy

- `main` - Production-ready code, protected branch
- `develop` - Integration branch for features (if used)
- `feature/*` - Feature branches (e.g., `feature/add-user-notifications`)
- `fix/*` - Bug fix branches (e.g., `fix/translation-cache-issue`)
- `docs/*` - Documentation updates

**Naming convention:**
```
feature/short-description
fix/issue-number-description
docs/what-you-updated
```

### Commit Messages

Follow conventional commit format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring (no feature change)
- `test`: Adding or updating tests
- `chore`: Maintenance tasks (dependencies, build config)
- `perf`: Performance improvements

**Examples:**
```
feat(auth): add refresh token rotation

Implements automatic refresh token rotation on login and
refresh endpoints for improved security.

Closes #123
```

```
fix(translation): handle missing cache gracefully

Fixes issue where translation service crashes when Redis
is unavailable by adding fallback logic.
```

## Code Style

### Backend (Python)

**Formatting and Linting:**
- **Formatter**: Black (line length: 100)
- **Linter**: Ruff (replaces flake8, isort, and more)

**Running formatters:**
```bash
# Format all Python files
docker compose exec backend black app/ tests/

# Lint with Ruff
docker compose exec backend ruff check app/ tests/

# Auto-fix Ruff issues
docker compose exec backend ruff check --fix app/ tests/
```

**Style Guidelines:**
- Use type hints for all function parameters and return values
- Prefer async/await for I/O operations
- Use Pydantic models for data validation
- Keep functions focused (single responsibility principle)
- Use descriptive variable names (no single-letter variables except loop counters)

**Example:**
```python
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.message import MessageResponse

async def get_messages(
    db: AsyncSession,
    channel_id: int,
    limit: int = 50,
    offset: int = 0,
) -> List[MessageResponse]:
    """
    Retrieve messages for a specific channel with pagination.

    Args:
        db: Database session
        channel_id: ID of the channel to fetch messages from
        limit: Maximum number of messages to return
        offset: Number of messages to skip

    Returns:
        List of message response objects
    """
    # Implementation here
    pass
```

### Frontend (TypeScript/React)

**Linting:**
- **Linter**: ESLint with TypeScript and React Hooks plugins
- **Style**: Follows React best practices and TypeScript strict mode

**Running linter:**
```bash
# Lint frontend code (from frontend directory)
docker compose exec frontend npm run lint

# Note: Frontend container runs in production mode by default
# For development with linting, you may need to run:
cd frontend && npm run dev
```

**Style Guidelines:**
- Use functional components with hooks (no class components)
- Prefer TypeScript interfaces for props and state
- Use meaningful component and variable names
- Extract reusable logic into custom hooks
- Keep components small and focused
- Use Zustand for global state management
- Use React Query for server state
- Follow React Hooks rules (use ESLint plugin)

**Component Structure:**
```typescript
import React from 'react';

interface MessageCardProps {
  messageId: string;
  content: string;
  timestamp: Date;
  onDelete?: (id: string) => void;
}

export const MessageCard: React.FC<MessageCardProps> = ({
  messageId,
  content,
  timestamp,
  onDelete,
}) => {
  // Component logic here
  return (
    <div className="message-card">
      {/* JSX here */}
    </div>
  );
};
```

**Styling:**
- Use Tailwind CSS utility classes
- Follow mobile-first responsive design
- Maintain consistent spacing and color schemes

### General Guidelines

- **No console.log or print statements**: Remove debugging statements before committing
- **Error handling**: Always handle errors gracefully with try/catch and user-friendly messages
- **Comments**: Write self-documenting code; add comments only for complex logic
- **File organization**: Keep files focused on a single responsibility
- **Naming conventions**:
  - Python: `snake_case` for functions/variables, `PascalCase` for classes
  - TypeScript: `camelCase` for functions/variables, `PascalCase` for components/interfaces

## Testing

### Backend Tests

**Running all tests:**
```bash
docker compose exec backend pytest
```

**Running specific tests:**
```bash
docker compose exec backend pytest tests/test_auth_login.py
docker compose exec backend pytest tests/test_auth_login.py::test_login_success
```

**Running with coverage:**
```bash
docker compose exec backend pytest --cov=app --cov-report=html
```

**Test Structure:**
- Tests are located in `backend/tests/`
- Use `pytest` with `pytest-asyncio` for async tests
- Use fixtures from `conftest.py` for common setup
- Mock external services (Telegram, OpenAI) in tests

**Writing Tests:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_channel(async_client: AsyncClient, auth_headers: dict):
    """Test channel creation endpoint."""
    response = await async_client.post(
        "/api/channels",
        json={"name": "Test Channel", "url": "https://t.me/testchannel"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Channel"
```

### Frontend Tests

**Running E2E tests:**
```bash
cd frontend
npm run test:e2e
```

**Test Structure:**
- E2E tests use Playwright
- Tests are located in `frontend/tests/` (if present)

### Manual Testing

Refer to the following guides for manual testing procedures:
- `MANUAL_TESTING_GUIDE.md` - Comprehensive testing procedures
- `TESTING_README.md` - Testing strategy overview
- `SECURITY_VERIFICATION_GUIDE.md` - Security-focused testing

### Continuous Integration

All pull requests automatically run:
- Backend unit tests with pytest
- Frontend build validation
- Code quality checks (see `.github/workflows/ci.yml`)

Ensure all CI checks pass before requesting review.

## Pull Request Process

### Before Submitting

1. **Update your branch:**
   ```bash
   git checkout main
   git pull origin main
   git checkout your-feature-branch
   git rebase main
   ```

2. **Run all tests:**
   ```bash
   docker compose exec backend pytest
   ```

3. **Check code style:**
   ```bash
   docker compose exec backend black --check app/ tests/
   docker compose exec backend ruff check app/ tests/
   ```

4. **Update documentation:** If your changes affect:
   - API endpoints → Update `docs/ARCHITECTURE.md` or API docs
   - Data flow → Update `docs/DATA_FLOW.md`
   - User features → Update `README.md`

5. **Add tests:** New features and bug fixes should include tests

### Submitting a Pull Request

1. **Push your branch:**
   ```bash
   git push origin your-feature-branch
   ```

2. **Create a Pull Request** on GitHub with:
   - **Title**: Clear, concise description (e.g., "Add email notification system")
   - **Description**:
     ```markdown
     ## Summary
     Brief description of changes

     ## Changes
     - Bullet point list of specific changes
     - Reference any related issues (#123)

     ## Testing
     - Describe how you tested the changes
     - List any manual testing steps required

     ## Screenshots (if applicable)
     Include screenshots for UI changes
     ```

3. **Link related issues:** Use keywords like "Closes #123" or "Fixes #456"

4. **Request review:** Assign reviewers and add appropriate labels

### Review Process

1. **Automated checks:** Ensure CI passes (tests, build)
2. **Code review:** Address reviewer feedback promptly
3. **Update as needed:** Push additional commits to your branch
4. **Approval:** At least one approval required for merge
5. **Merge:** Maintainers will merge once approved

### After Merge

- **Delete your branch:**
  ```bash
  git branch -d your-feature-branch
  git push origin --delete your-feature-branch
  ```

- **Update your local main:**
  ```bash
  git checkout main
  git pull origin main
  ```

## Architecture and Design

Before making significant changes, familiarize yourself with the project architecture:

### Key Documentation

- **[Architecture Overview](docs/ARCHITECTURE.md)** - System components, services, and infrastructure
- **[Data Flow Guide](docs/DATA_FLOW.md)** - Message processing pipeline and data flows

### Architectural Principles

- **Service Layer Pattern**: Business logic in service modules (`app/services/`)
- **Repository Pattern**: Database access via SQLAlchemy models (`app/models/`)
- **Dependency Injection**: FastAPI's DI for sessions, auth, services
- **Async-First**: Use async/await for all I/O operations
- **API-First Design**: RESTful endpoints with clear contracts

### Key Services

- **Translation Service** (`app/services/llm_translator.py`) - LLM-based translation with caching
- **Telegram Client** (`app/services/telegram_client.py`) - Telegram API integration with rate limiting
- **Cache Service** (`app/services/cache_service.py`) - Redis-backed caching with adaptive TTL
- **Message Processing** (`app/jobs/collect_messages.py`) - Background message collection

## Common Tasks

### Adding a New API Endpoint

1. **Define Pydantic schemas** in `backend/app/schemas/`:
   ```python
   # app/schemas/your_model.py
   from pydantic import BaseModel

   class YourModelCreate(BaseModel):
       name: str
       description: str

   class YourModelResponse(BaseModel):
       id: int
       name: str
       description: str
   ```

2. **Create SQLAlchemy model** in `backend/app/models/`:
   ```python
   # app/models/your_model.py
   from sqlalchemy import Column, Integer, String
   from app.database import Base

   class YourModel(Base):
       __tablename__ = "your_models"

       id = Column(Integer, primary_key=True, index=True)
       name = Column(String, nullable=False)
       description = Column(String)
   ```

3. **Create API endpoint** in `backend/app/api/`:
   ```python
   # app/api/your_resource.py
   from fastapi import APIRouter, Depends
   from sqlalchemy.ext.asyncio import AsyncSession
   from app.database import get_async_db
   from app.schemas.your_model import YourModelCreate, YourModelResponse

   router = APIRouter(prefix="/api/your-resource", tags=["Your Resource"])

   @router.post("/", response_model=YourModelResponse)
   async def create_your_model(
       data: YourModelCreate,
       db: AsyncSession = Depends(get_async_db),
   ):
       # Implementation
       pass
   ```

4. **Register router** in `backend/app/main.py`:
   ```python
   from app.api import your_resource
   app.include_router(your_resource.router)
   ```

5. **Create database migration:**
   ```bash
   docker compose exec backend alembic revision --autogenerate -m "Add your_models table"
   docker compose exec backend alembic upgrade head
   ```

6. **Add tests** in `backend/tests/test_your_resource.py`

### Adding a New Background Job

1. **Create job file** in `backend/app/jobs/your_job.py`:
   ```python
   import logging
   from app.database import AsyncSessionLocal

   logger = logging.getLogger(__name__)

   async def your_scheduled_job():
       """Your job description."""
       async with AsyncSessionLocal() as db:
           # Job implementation
           logger.info("Job completed successfully")
   ```

2. **Register in scheduler** (`backend/app/main.py`):
   ```python
   from app.jobs.your_job import your_scheduled_job

   scheduler.add_job(
       your_scheduled_job,
       "cron",
       hour=2,
       minute=0,
       id="your_job_id",
   )
   ```

### Adding a Frontend Component

1. **Create component** in `frontend/src/components/`:
   ```typescript
   // src/components/YourComponent.tsx
   import React from 'react';

   interface YourComponentProps {
     title: string;
   }

   export const YourComponent: React.FC<YourComponentProps> = ({ title }) => {
     return (
       <div className="p-4">
         <h2 className="text-xl font-bold">{title}</h2>
       </div>
     );
   };
   ```

2. **Add to routing** (if needed) in `frontend/src/App.tsx`

3. **Create API hook** with React Query:
   ```typescript
   // src/hooks/useYourData.ts
   import { useQuery } from '@tanstack/react-query';
   import axios from 'axios';

   export const useYourData = () => {
     return useQuery({
       queryKey: ['your-data'],
       queryFn: async () => {
         const { data } = await axios.get('/api/your-endpoint');
         return data;
       },
     });
   };
   ```

## Getting Help

- **Issues**: Search existing issues or create a new one on GitHub
- **Documentation**: Check `docs/` directory for detailed guides
- **Architecture Questions**: Refer to [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Security Concerns**: See [SECURITY_VERIFICATION_GUIDE.md](SECURITY_VERIFICATION_GUIDE.md)

### Maintainers

For questions or clarifications, tag maintainers in your issue or PR:
- @yourusername - Project lead

---

**Thank you for contributing to OSFeed!** Your efforts help build a better OSINT platform for everyone.
