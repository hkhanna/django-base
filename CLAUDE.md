# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Local Setup
- `make all` - Full setup with local database (clean, build, db setup)
- `make all-docker` - Full setup with Docker database
- `make build` - Install Python dependencies, npm packages, and playwright

### Running the Application
- `make run` - Start both Django dev server and Vite dev server
- `make app` - Start only Django dev server on port specified in .env
- `make vite` - Start only Vite dev server for frontend

### Testing and Quality
- `make check` - Run all tests including mypy, tsc, and pytest
- `make mypy` - Run Python type checking
- `make tsc` - Run TypeScript type checking  
- `make playwright` - Run E2E tests in headed mode
- `py.test -n auto` - Run pytest with parallel execution

### Database Operations
- `make db` - Clear database, run migrations, and seed data
- `make migrate` - Run Django migrations only
- `make seed` - Seed database with initial data
- `make docker-db` - Start PostgreSQL in Docker container

### Other Utilities
- `make shell` - Start Django shell_plus
- `make fmt` - Format HTML templates with djhtml

## Architecture Overview

### Backend (Django)
- **Custom User Model**: Email-based authentication using `core.User` (no username field)
- **Service Pattern**: Business logic in `core/services.py`, data access in `core/selectors.py`
- **Model Protection**: BaseModel enforces use of services via `_allow_save` flag
- **Multi-tenancy Ready**: Org/User relationship with settings hierarchy (Global → Plan → Org → OrgUser)
- **Email System**: Comprehensive email tracking with PostMark integration and webhook handling
- **Event System**: Event logging for audit trails and integrations

### Frontend (React + Inertia.js)
- **Tech Stack**: React, TypeScript, TailwindCSS, Shadcn UI components
- **Build System**: Vite with hot reload, builds to `frontend/dist/`
- **Styling**: TailwindCSS with mobile-first responsive design
- **State**: Inertia.js handles server-client state synchronization

### Key Models
- `User`: Email-based auth with display_name, email_history
- `Org`: Organizations with domain-based routing, plans, and settings
- `Plan`: Feature sets tied to billing with hierarchical settings
- `EmailMessage`: Complete email audit trail with attachments and webhooks
- `Event`: System-wide event logging

### Settings System
Complex hierarchical settings system:
1. **GlobalSetting**: System-wide defaults
2. **PlanOrgSetting**: Plan-specific org settings (billing limits)
3. **OverriddenOrgSetting**: Org-specific overrides
4. **OrgUserSetting**: User preference definitions
5. **OrgUserOrgUserSetting**: Individual user values
6. **OrgUserSettingDefault**: Org defaults for user settings

### Important Patterns
- **Services Layer**: Never save models directly - use services in `core/services.py`
- **Model Validation**: Custom `clean()` methods with proper error handling
- **UUID Primary Keys**: All models use UUIDs for external references
- **Host-based Routing**: `HOST_URLCONFS` for multi-domain support
- **Celery Integration**: Background tasks with Redis broker
- **Security**: CSRF protection, secure headers, request ID tracking

## Development Guidelines

### General Principles
- Focus on readability over performance
- Write correct, bug-free, fully functional code
- Leave NO todos, placeholders, or missing pieces
- Always reference file names when discussing code
- Be concise and minimize prose
- If uncertain about correctness, say so rather than guessing

### Backend Development (Django/Python)
- **Code Style**: Follow PEP 8, use descriptive variable/function names with underscores
- **Django Patterns**: Leverage built-in features, follow MVT pattern strictly
- **Data Access**: Use functions in `core/services.py` and `core/selectors.py` instead of ORM directly
- **Forms**: Use Django form and model form classes for validation
- **Error Handling**: Implement at view level, use try-except blocks, Django's validation framework
- **Architecture**: Keep business logic in services/selectors, views light (request handling only), models light
- **Testing**: Use pytest, pytest-django for quality assurance
- **URLs**: Define clear, RESTful patterns in urls.py
- **Performance**: Use select_related/prefetch_related, implement database indexing
- **Static Files**: Optimize with Django's management system (WhiteNoise/CDN)

### Frontend Development (React/TypeScript)
- **Component Library**: Use Shadcn UI components, modify as necessary
- **Styling**: TailwindCSS with mobile-first responsive design
- **Architecture**: Functional/declarative patterns, avoid classes
- **Code Organization**: Prefer iteration and modularization over duplication
- **Naming**: Use auxiliary verbs (isLoading, hasError), lowercase-with-dashes for directories
- **Exports**: Favor named exports for components
- **TypeScript**: Use interfaces over types, avoid enums (use maps), functional components
- **Syntax**: Use "function" keyword for pure functions, avoid unnecessary curly braces
- **File Structure**: exported component → subcomponents → helpers → static content → types
- **Error Handling**: Early returns, guard clauses, proper logging, user-friendly messages
- **Validation**: Use Zod for forms, model expected errors as return values
- **UI Components**: Shadcn UI, Radix, Tailwind Aria

### Environment Setup
- Requires PostgreSQL 16, Python 3.13, libtidy-dev
- Settings split: `common.py`, `local.py`, `production.py`, `test.py`
- Environment variables in `.env` file (copy from `.env.example`)
- Default superuser: `admin@localhost` / `admin`

### Frontend Development
- Components in `frontend/src/components/` following functional patterns
- Pages in `frontend/src/pages/core/` for Inertia.js routing
- Custom hooks in `frontend/src/hooks/`
- Type definitions in `frontend/src/types/`
- Uses Shadcn UI component library with Radix primitives

### Testing
- Backend: pytest with pytest-django, factory-boy for fixtures
- Frontend: TypeScript compilation checking
- E2E: Playwright tests in `*/tests/test_playwright.py`
- Test settings module: `config.settings.test`

### Deployment
- Render.com deployment via `render.yaml`
- Heroku-compatible with `Procfile` and build scripts
- Auto-deploy on push to `origin/main`
- Static files handled by Django with Vite build integration