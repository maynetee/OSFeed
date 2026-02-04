# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2024-01-01

### Added
- Telegram collection with flood-wait handling
- LLM translation with model routing (Gemini Flash default, GPT-4o-mini for high-priority)
- Vector deduplication (Qdrant) and semantic search capabilities
- Daily digests v2 with HTML and PDF export
- Key entity extraction in digests
- Collections system to group channels
- Collection-based digest filtering and message exports
- Collection statistics dashboard
- Collection sharing (viewer/editor/admin roles)
- Collection alerts and in-app notifications
- KPI dashboard with messages, channels, and duplicate metrics
- CSV export for KPI data
- Frontend built with React 18, Vite, Tailwind CSS, Zustand, and React Query
- Command palette (⌘K) with global keyboard shortcuts
- Virtualized message feed with lazy-loaded routes
- Full-text and semantic search functionality
- Similar-message view for deduplication
- Message exports in CSV, PDF, and HTML formats
- Digest history pagination
- Collection-aware search filters
- Trust indicators (duplicate score, primary source)
- Internationalization (i18n) support for French and English
- Progressive Web App (PWA) with offline installation
- Redis cache for translations (persistent)
- Audit logs for sensitive actions (RGPD compliance)
- Refresh tokens with session rotation
- API usage tracking for LLM cost monitoring
- Docker and Docker Compose support for easy deployment
- PostgreSQL database with Alembic migrations
- Authentication system with JWT tokens
- RBAC (Role-Based Access Control) for user permissions

### Security
- Session rotation mechanism
- Refresh token implementation
- Audit logging for sensitive actions
- RGPD compliance features

---

## How to Maintain This Changelog

When making changes to the project, update the `[Unreleased]` section under the appropriate category:

- **Added** for new features
- **Changed** for changes in existing functionality
- **Deprecated** for soon-to-be removed features
- **Removed** for now removed features
- **Fixed** for any bug fixes
- **Security** for vulnerability fixes and security improvements

When releasing a new version:
1. Create a new version heading below `[Unreleased]` with the version number and date
2. Move all items from `[Unreleased]` to the new version section
3. Leave `[Unreleased]` empty but with all category headers intact

### Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR** version for incompatible API changes
- **MINOR** version for backwards-compatible new features
- **PATCH** version for backwards-compatible bug fixes

[Unreleased]: https://github.com/yourusername/osfeed/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/osfeed/releases/tag/v0.1.0
