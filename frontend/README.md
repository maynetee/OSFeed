# OSFeed Frontend

Modern React frontend for OSFeed built with React 18, Vite, TypeScript, Tailwind CSS, and Zustand for state management.

## Features

- **Modern Stack**: React 18 + Vite + TypeScript + Tailwind CSS
- **State Management**: Zustand + React Query for server state
- **Command Palette**: Global keyboard shortcuts (⌘K) for power users
- **Virtualized Feed**: High-performance message list with infinite scroll
- **Lazy Routes**: Code-split routes for faster initial load
- **Search**: Full-text + semantic search with collection filters
- **Internationalization**: FR/EN support with react-i18next
- **PWA Ready**: Offline-capable progressive web app
- **Exports**: CSV/PDF/HTML message exports
- **Trust Indicators**: Duplicate scores and primary source badges
- **Dark Mode**: Full dark mode support
- **Responsive**: Mobile-first design

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000`

### Installation

```bash
npm install
```

### Development

Start the development server with hot-reloading:

```bash
npm run dev
```

The app will be available at http://localhost:5173

## Available Scripts

| Command | Description |
|---------|-------------|
| `npm run dev` | Start development server with hot-reload |
| `npm run build` | Build for production (TypeScript + Vite) |
| `npm run preview` | Preview production build locally |
| `npm run lint` | Run ESLint checks |
| `npm run type-check` | Run TypeScript type checking |
| `npm run test:e2e` | Run Playwright E2E tests |
| `npm run test:e2e:ui` | Run E2E tests with Playwright UI |

## Architecture Overview

```
src/
  app/                Application setup
    i18n.ts          Internationalization configuration
    providers.tsx    React providers (QueryClient, i18n)
    router.tsx       React Router configuration

  components/         Reusable UI components
    ui/              Primitive components (buttons, cards, dialogs)
    layout/          Shell, sidebar, header, command palette
    messages/        Message cards, filters, virtualized feed
    digests/         Digest cards and viewer
    collections/     Collection management components
    search/          Search interface and filters

  features/           Feature-specific pages and logic
    auth/            Login, registration, password reset
    dashboard/       Main dashboard and KPIs
    messages/        Message feed and detail views
    digests/         Digest history and viewer
    collections/     Collection management
    channels/        Channel management
    settings/        User settings and preferences

  hooks/              Global custom hooks
    useAuth.ts       Authentication state and actions
    useTheme.ts      Dark mode toggle
    useDebounce.ts   Debounced values
    useKeyboard.ts   Keyboard shortcut handlers

  lib/                Utilities and API client
    api.ts           Axios API client setup
    queryClient.ts   React Query configuration
    utils.ts         Helper functions

  stores/             Zustand state stores
    authStore.ts     Authentication state
    uiStore.ts       UI state (sidebar, modals)
    searchStore.ts   Search filters and state

  styles/             Global styles
    globals.css      Tailwind imports and custom styles
```

## Component Documentation

### UI Primitives (`src/components/ui`)

Base components built on Radix UI and styled with Tailwind:

- **Button**: Primary, secondary, outline, ghost variants
- **Card**: Content containers with header/footer
- **Dialog**: Modal dialogs and drawers
- **Input**: Text inputs with validation states
- **Select**: Dropdown selects
- **Badge**: Status indicators and tags
- **Tooltip**: Hover tooltips
- **Tabs**: Tabbed interfaces
- **Toast**: Toast notifications

### Layout Components (`src/components/layout`)

- **Shell**: Main application layout wrapper
- **Sidebar**: Navigation sidebar with collections
- **Header**: Top bar with search, notifications, user menu
- **CommandPalette**: ⌘K command palette for quick actions
- **NotificationDropdown**: In-app notification center

### Message Components (`src/components/messages`)

- **MessageCard**: Individual message display with metadata
- **MessageFeed**: Virtualized infinite-scroll message list
- **MessageFilters**: Search and filter controls
- **MessageDetail**: Full message view with actions
- **TrustIndicator**: Duplicate score and primary source badges

### Digest Components (`src/components/digests`)

- **DigestCard**: Digest preview card
- **DigestViewer**: Full digest reader with HTML/PDF export
- **DigestHistory**: Paginated digest history list

## Internationalization (i18n)

OSFeed frontend supports French and English with `react-i18next`.

### Configuration

i18n setup is in `src/app/i18n.ts` with translations in `src/locales/`:

```
src/locales/
  en/
    translation.json
  fr/
    translation.json
```

### Language Persistence

The active language is stored in `localStorage` under the key `osfeed_language`.

### Usage in Components

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t, i18n } = useTranslation();

  return (
    <div>
      <h1>{t('welcome.title')}</h1>
      <button onClick={() => i18n.changeLanguage('fr')}>
        Français
      </button>
    </div>
  );
}
```

### Language Toggle

The language switcher is in the header and command palette (⌘K → "Change language").

## Message Exports

OSFeed supports exporting messages in multiple formats through the backend API:

### Export Formats

| Format | Endpoint | Description |
|--------|----------|-------------|
| **CSV** | `/api/messages/export/csv` | Spreadsheet format with all metadata |
| **PDF** | `/api/messages/export/pdf` | Formatted PDF document |
| **HTML** | `/api/messages/export/html` | Standalone HTML file |

### Export Filters

Exports respect all active filters:

- Collection scope
- Date range
- Search query
- Channel filter
- Language filter
- Duplicate filter

### Usage

Click "Export" in the message feed toolbar and select your format. The export will be generated server-side and downloaded automatically.

## Search Functionality

### Full-Text Search

Standard keyword search across message content and titles:

```typescript
// Searches message text and channel names
GET /api/messages/search?q=keyword&collection_id=123
```

### Semantic Search

AI-powered similarity search using embeddings:

```typescript
// Find semantically similar messages
GET /api/messages/semantic-search?q=query&collection_id=123
```

### Search Filters

- **Collections**: Scope to specific collections
- **Date Range**: Filter by date posted
- **Channels**: Filter by source channels
- **Languages**: Filter by detected language
- **Duplicates**: Show/hide duplicate messages

## Global Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open command palette |
| `⌘/` / `Ctrl+/` | Focus search |
| `⌘B` / `Ctrl+B` | Toggle sidebar |
| `⌘N` / `Ctrl+N` | New collection |
| `Esc` | Close dialogs/modals |
| `G then D` | Go to dashboard |
| `G then M` | Go to messages |
| `G then C` | Go to collections |

## E2E Testing

Playwright tests cover critical user flows:

### Test Coverage

- **Authentication**: Login, logout, registration
- **Navigation**: Main routes and navigation
- **Message Feed**: Loading, scrolling, filtering
- **Collections**: Create, edit, delete
- **Exports**: Export dialog and format selection
- **Command Palette**: Open, search, execute commands

### Running Tests

```bash
# Run all tests headless
npm run test:e2e

# Run with UI for debugging
npm run test:e2e:ui

# Run specific test file
npx playwright test e2e/auth.spec.ts
```

### Test Files

```
e2e/
  auth.spec.ts         Authentication flows
  messages.spec.ts     Message feed and detail
  collections.spec.ts  Collection management
  exports.spec.ts      Export functionality
  navigation.spec.ts   Route navigation
```

## State Management

### Zustand Stores

- **authStore**: User authentication state and token management
- **uiStore**: UI state (sidebar open/closed, active modals)
- **searchStore**: Search filters and query state

### React Query

Server state is managed with React Query for:

- Automatic caching and revalidation
- Optimistic updates
- Background refetching
- Request deduplication

Example query hook:

```typescript
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useMessages(collectionId?: string) {
  return useQuery({
    queryKey: ['messages', collectionId],
    queryFn: () => api.get(`/messages?collection_id=${collectionId}`),
    staleTime: 30000, // 30 seconds
  });
}
```

## PWA Configuration

The app is configured as a Progressive Web App (PWA) with:

- Offline support via service worker
- Install prompt for mobile/desktop
- App manifest with icons
- Background sync for offline actions

Users can install OSFeed as a standalone app from their browser.

## Development Tips

### Hot Module Replacement

Vite provides instant HMR. Changes to React components update without full page reload.

### Type Safety

Run TypeScript checks before committing:

```bash
npm run type-check
```

### Linting

Ensure code quality with ESLint:

```bash
npm run lint
```

### API Proxy

The Vite dev server proxies `/api/*` requests to `http://localhost:8000` (configured in `vite.config.ts`).

## Build for Production

```bash
npm run build
```

This creates an optimized build in `dist/`:

- Minified and tree-shaken JavaScript
- Optimized CSS
- Asset compression
- Source maps for debugging

Preview the production build locally:

```bash
npm run preview
```

## Environment Variables

Create a `.env.local` file for local overrides:

```bash
# API base URL (default: http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000

# Enable debug mode
VITE_DEBUG=true
```

All environment variables must be prefixed with `VITE_` to be exposed to the frontend.

## Troubleshooting

### Port Already in Use

If port 5173 is occupied, Vite will use the next available port. Check the terminal output for the actual URL.

### API Connection Errors

Ensure the backend is running on `http://localhost:8000` and accessible from the frontend.

### Build Errors

Clear the Vite cache and reinstall dependencies:

```bash
rm -rf node_modules dist .vite
npm install
npm run build
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines and contribution instructions.

## License

See [LICENSE](../LICENSE) for license information.
