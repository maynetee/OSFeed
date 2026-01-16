# TeleScope Frontend

## Demarrage

```bash
npm install
npm run dev
```

## Scripts utiles

- `npm run build` : build production (TypeScript + Vite)
- `npm run preview` : preview de la build
- `npm run test:e2e` : tests Playwright

## Architecture rapide

```
src/
  app/            providers, router, i18n
  components/     UI reutilisable + layout
  features/       pages par domaine
  hooks/          hooks globaux
  lib/            client API + helpers
  stores/         stores Zustand
  styles/         styles globaux
```

## Documentation composants

- `src/components/ui` : primitives (boutons, cartes, dialogues)
- `src/components/layout` : shell, sidebar, header, palette de commandes
- `src/components/messages` : cartes messages, filtres, feed virtualise
- `src/components/digests` : cartes et viewer de digest

## Internationalisation

- Les libelles utilisent `react-i18next` (`src/app/i18n.ts`).
- La langue active est stockee dans `localStorage` via `telescope_language`.

## Exports

- CSV via `/api/messages/export/csv`
- PDF via `/api/messages/export/pdf`
- HTML via `/api/messages/export/html`

## Tests E2E

Les tests Playwright couvrent le login, la navigation principale et l'ouverture du dialogue d'export.
