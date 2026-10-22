# Heketon Monorepo

Monorepo containing the **Next.js (TailAdmin + Vercel AI SDK)** frontend and **FastAPI (MVC + LangChain/LangGraph + Async SQLAlchemy/Alembic)** backend, configured with a **single shared root `.env`** and standalone Dockerfiles.

## Repository Structure

```text
Heketon/
├── backend/                # FastAPI Backend (managed with uv)
│   ├── alembic/            # Async Alembic database migrations
│   ├── app/
│   │   ├── agent/          # LangChain & LangGraph AI Agents
│   │   ├── constant/       # App-wide constants & enums
│   │   ├── controller/     # FastAPI Controllers / API Routers
│   │   ├── core/           # Config (reads root ../.env) & JWT/Argon2 Security
│   │   ├── db/             # Async SQLAlchemy 2.0 Session & Engine
│   │   ├── dto/            # Pydantic DTOs / Schemas (BaseDTO, ApiResponse)
│   │   ├── exception/      # Custom exceptions & handlers
│   │   ├── middleware/     # Custom FastAPI middlewares
│   │   ├── model/          # SQLAlchemy ORM Models (Base, BaseModel)
│   │   ├── repository/     # Async Generic CRUD Repository (BaseRepository)
│   │   ├── service/        # Business Logic Services
│   │   ├── util/           # Shared utility helpers
│   │   └── main.py         # FastAPI Application Entrypoint
│   ├── scripts/            # DB health check & seeding scripts (check_db.py, seed.py)
│   ├── tests/              # Pytest suite (unit/, integration/, conftest.py, test_health.py)
│   ├── Dockerfile          # Standalone FastAPI + uv container image
│   └── pyproject.toml
├── frontend/               # Next.js 16 TailAdmin Dashboard + Vercel AI SDK (pnpm)
│   ├── scripts/            # Frontend build/utility scripts
│   ├── src/
│   │   ├── app/
│   │   ├── components/
│   │   ├── constants/      # Frontend constants & endpoint routes
│   │   ├── lib/api.ts      # Fetch wrapper connected to NEXT_PUBLIC_API_URL
│   │   ├── services/       # API service modules
│   │   └── utils/          # Frontend utility functions
│   ├── tests/              # Frontend test suite
│   ├── Dockerfile          # Standalone multi-stage Next.js container image
│   ├── next.config.ts      # Loads shared root ../.env automatically
│   └── package.json
├── docs/                   # Project documentation & rulebook
├── scripts/                # Root automation scripts (setup.ps1, dev.ps1)
├── .env.example            # Shared monorepo environment template (FE + BE + Supabase)
└── docker-compose.yml      # Builds & runs standalone frontend + backend containers
```

## Shared Environment (`.env`)

Both `frontend/` and `backend/` read from the **single root `.env` file** (`Heketon/.env`):
- **Backend**: [`app/core/config.py`](backend/app/core/config.py) automatically resolves the root `.env` via `Path(__file__).resolve().parents[3] / ".env"` (ignoring `NEXT_PUBLIC_*` keys via `extra="ignore"`).
- **Frontend**: [`frontend/next.config.ts`](frontend/next.config.ts) automatically loads `../.env` using Node's native `process.loadEnvFile()`.
- **Security Rule**: Only variables prefixed with `NEXT_PUBLIC_` are bundled into the browser. Never prefix backend secrets (`DATABASE_URL`, `SECRET_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, LLM API keys) with `NEXT_PUBLIC_`.

## Quick Start

```powershell
# 1. Setup dependencies & root .env
.\scripts\setup.ps1

# 2. Launch Backend & Frontend dev servers
.\scripts\dev.ps1
```
