# AGENTS.md

This file provides guidance to AI Coding Agents when working with code in this repository.

## What this repo is

Monorepo for **Heketon**, an HR & Office Ops AI Orchestrator built for Tencent Cloud Hackathon Indonesia 2026 (Challenge B — "The Office Agent"). The product autonomously triages interview scheduling between an HR user, a hiring manager (email), and a candidate (WhatsApp/email), with mandatory human approval, undo window, and immutable audit logging.

`docs/ARCHITECTURE_AND_SPEC.md` is the **source of truth** for the intended system: the 5 accountability pillars (Sources, Permissions, Approval, Limits, Record), the LangGraph topology, and the full database schema. Most of it is **not implemented yet** — see "Current state" below.

## Commands

All commands run from the repo root unless noted. Windows-first setup scripts use PowerShell.

```powershell
# One-time setup: creates root .env from .env.example, uv sync, pnpm install
.\scripts\setup.ps1

# Run backend (:8000) and frontend (:3000) in separate windows
.\scripts\dev.ps1
```

### Backend (`backend/`, Python 3.12, uv)

```bash
cd backend
uv sync                                              # install deps
uv run fastapi dev app/main.py                       # dev server with reload
uv run pytest                                        # full suite
uv run pytest tests/test_health.py::test_health_check # single test
uv run pytest -k health                              # tests matching a name
uv run ruff check .                                  # lint
uv run ruff check --fix .
uv run alembic revision --autogenerate -m "message"  # new migration
uv run alembic upgrade head
uv run python -m scripts.check_db                    # verify Postgres + pgvector
uv run python -m scripts.seed                        # seed dev data (stub)
uv run python -m scripts.unseed                      # unseed/purge dev data (--keep-admin / --all / --dry-run)
```

### Frontend (`frontend/`, Next.js 16, pnpm, Node >= 20.9)

```bash
cd frontend
pnpm install
pnpm dev        # Turbopack dev server on :3000
pnpm build
pnpm lint       # eslint (next/core-web-vitals + typescript)
```

There is no frontend test runner configured; `frontend/tests/`, `e2e/`, and `.github/` are empty placeholders.

### Docker

```bash
docker compose up --build   # builds backend + frontend images, reads root .env
```

## Shared environment

Both apps read the **single root `.env`** (not per-app files):

- Backend: `backend/app/core/config.py` loads `Heketon/.env` via `Path(__file__).resolve().parents[3]`, with `backend/.env` as a fallback (used inside Docker). Settings are `pydantic-settings` with `extra="ignore"` so `NEXT_PUBLIC_*` keys are skipped.
- Frontend: `frontend/next.config.ts` calls `process.loadEnvFile("../.env")` at config load time.
- Only `NEXT_PUBLIC_*` reaches the browser. `NEXT_PUBLIC_API_URL` defaults to `http://localhost:8000/api/v1`; the browser calls FastAPI directly (no Next.js rewrite proxy), so CORS in `BACKEND_CORS_ORIGINS` must include the frontend origin.

## Backend architecture

Layered MVC under `backend/app/`; dependencies flow **controller → service → repository → model**, with Pydantic DTOs at the boundaries:

| Layer | Path | Role |
| --- | --- | --- |
| `controller/` | `*Controller.py` | FastAPI routers; mount under `settings.API_V1_STR` (`/api/v1`) with camelCase paths |
| `service/` | `*Service.py` | business logic; orchestration, validation, transaction boundaries |
| `repository/` | `*Repository.py` | data access; `BaseRepository[ModelType]` generic async CRUD, `selectinload` queries |
| `model/` | `*Model.py` | SQLAlchemy ORM; `Base`, `TableBaseModel`, `AppendOnlyBaseModel` |
| `dto/` | `*DTO.py` | Pydantic schemas; `BaseDTO`, `ApiResponse[T]`, `PaginatedResponse[T]` |
| `exception/` | `*Exception.py` | custom exceptions (`CustomException.py`) and global handlers (`ExceptionHandler.py`) |
| `agent/` | LangChain / LangGraph | state graph, nodes, tools |
| `core/` | `AppConfig.py`, `AppSecurity.py` | config (pydantic-settings), JWT + Argon2 |
| `db/` | `DatabaseSession.py` | async engine, session, `get_db` dependency |
| `middleware/`, `constant/`, `util/` | cross-cutting | CORS, timing, enums, timezone helpers |

Conventions that are easy to get wrong:

- **Strict CamelCase File Naming**: All functional backend files must be PascalCase/CamelCase (e.g. `CandidateController.py`, `CandidateService.py`, `CandidateRepository.py`, `CandidateDTO.py`, `CandidateModel.py`).
- **camelCase Route URLs**: Endpoint paths under `/api/v1` use camelCase (e.g. `/api/v1/operationalRules`, `/api/v1/actionPlans`, `/api/v1/slotConflictChecker/check`).
- `BaseModel` / `TableBaseModel` (`app/model/BaseModel.py`) supplies integer PK `nid` (or UUID `id`), `dcrea`, `dmod`, and a `MetaData` naming convention — every new model inherits it.
- `BaseRepository` uses PEP 695 generics (`class BaseRepository[ModelType: Base]`) and commits inside `create`/`update`/`delete`, so services must not assume an open transaction after those calls.
- API responses are wrapped in `ApiResponse[T]` (`success`, `message`, `data`) and `PaginatedResponse[T]` (`items`, `total`, `page`, `page_size`, `total_pages`).
- `app/main.py` mounts all 16 modular routers under `/api/v1` with `TAGS_METADATA` registered for Swagger UI at `/docs`.
- Alembic autogenerate sees all models via `app/model/__init__.py`. Migration revision is currently at `00676c75559c`.
- Database is PostgreSQL + `pgvector`; `LANGGRAPH_CHECKPOINT_DB_URI` (sync DSN) is separate from `DATABASE_URL` (asyncpg DSN) and is intended for the Postgres checkpointer.
- LLM providers already in `pyproject.toml`: OpenAI, Google GenAI, Anthropic, Groq, Ollama. Do not add a provider package without checking first.

### Intended LangGraph flow (from the spec)

`guardrail (injection scan) → retriever (contacts/calendar/rules with source IDs) → planner (triage, max 3 rounds) → secondary validator → human approval gate (interrupt) → 60s undo buffer → executor → audit logger`.

Key invariants to preserve when implementing: external sends and calendar writes require `ActionPlan.status == APPROVED`; ambiguity or `negotiation_round > 3` halts to human clarification; every plan carries `sources_cited`; every transition writes to `audit_logs`. Domain entities: `Contact`, `CandidateApplication`, `CalendarEvent`, `OperationalRule`, `NegotiationThread`, `ActionPlan`, `ActionItem`, `MessageLog`, `AuditLog`. Timezone handling is WIB/WITA/WIT with working hours 09:00–17:00 and Friday prayer 11:30–13:00 blocked.

## Frontend architecture

TailAdmin Pro template (Next.js 16 App Router, React 19, Tailwind v4) extended for this project. `frontend/AGENTS.md` holds the detailed component/styling rules — follow it when editing under `frontend/`.

- Routes live only under `src/app/[locale]/`. Route groups: `(admin)` (sidebar + header shell), `(full-width-pages)` (auth/error, no shell), `(layouts-example)`. Never create pages directly under `src/app/`.
- i18n via next-intl: `src/i18n/routing.ts` currently declares **only `en`** with `localePrefix: "never"`; `src/messages/en.json` is the only dictionary. Import `Link`/`useRouter`/`usePathname`/`redirect` from `@/i18n/navigation`, never from `next/*`. New locales require edits to `routing.ts`, `languages.ts`, and a matching `messages/<locale>.json`.
- `src/proxy.ts` is the Next.js 16 middleware (renamed to `proxy`), running next-intl routing.
- API access: `src/lib/api.ts` (`apiFetch<T>`, `ApiError`) prepends `NEXT_PUBLIC_API_URL`, injects JSON + optional bearer token, and surfaces FastAPI's `detail` and `message`. Endpoint constants go in `src/constants/index.ts`; typed service modules belong in `src/services/` (currently empty barrel).
- UI conventions: `@/*` → `src/*`; components are PascalCase with default exports; icons come from the `@/icons` barrel (SVGs compiled via SVGR); charts (`react-apexcharts`), FullCalendar, and Swiper must be dynamically imported with `ssr: false`.
- Tailwind v4 has **no `tailwind.config`** — theme tokens and third-party overrides live in `src/app/globals.css` under `@theme`. Use theme tokens, `dark:` variants on every styled element, and CSS logical properties (`ms-*`, `pe-*`, `start-*`, `text-start`, …) instead of physical `ml-*`/`left-*` so RTL keeps working.
- Global state stays in `ThemeContext` and `SidebarContext`; modals use `useModal`.

## Current state (what exists vs. spec)

Implemented:
- Monorepo scaffolding, shared `.env` loading, async DB session/engine (`DatabaseSession.py`), base ORM models (`BaseModel.py`), generic repository (`BaseRepository.py`), base DTOs (`BaseDTO.py`).
- 16 modular standalone CamelCase controllers, services, repositories, DTOs, and ORM models.
- OpenAPI metadata tags and 16 routers mounted in `app/main.py`.
- Alembic async migrations up to `06784f3e4d33` (`06784f3e4d33_add_orchestration_and_extended_model_.py`).
- Complete automated test suite: 36 tests passing (unit tests + integration tests covering all 16 domains).
- Technical documentation suite in `docs/backend/` (`ARCHITECTURE_AND_STRUCTURE.md`, `API_CONTRACTS.md`, `DATABASE_AND_MIGRATIONS.md`, `TESTING_AND_DEVELOPMENT.md`).
- TailAdmin UI shell, `apiFetch` client, and Docker images.

Not yet implemented:
- Full LangGraph agent graph in `app/agent/`.
- Frontend feature pages wired to backend API endpoints.
