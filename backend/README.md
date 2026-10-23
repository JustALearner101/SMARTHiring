# Heketon Backend

FastAPI asynchronous backend for **Heketon** (HR & Office Ops AI Orchestrator), built for the Tencent Cloud Hackathon Indonesia 2026. The backend orchestrates autonomous schedule triage, multi-agent evaluation, candidate escalation, and human-in-the-loop approvals across WhatsApp and Email.

---

## Architecture Overview

The backend uses a strict **Layered MVC Architecture** located under `app/`. Dependencies strictly flow unidirectionally:

$$\text{Controller (HTTP)} \longrightarrow \text{Service (Logic)} \longrightarrow \text{Repository (Data Access)} \longrightarrow \text{Model (SQLAlchemy)}$$

```
backend/
├── alembic/                # Database migrations (async SQLAlchemy schema versioning)
├── app/
│   ├── agent/              # LangGraph multi-agent topology, nodes, tools & ADK
│   │   └── adk/            # Experimental Google ADK sub-agent (feature-flagged)
│   ├── constant/           # Application-wide constants & enums
│   ├── controller/         # FastAPI routers (mounted under /api/v1)
│   ├── core/               # Configuration (Pydantic Settings), security & JWT
│   ├── db/                 # Async database session & engine management
│   ├── dto/                # Pydantic data transfer objects (request/response)
│   ├── exception/          # Custom exceptions & HTTP exception handlers
│   ├── middleware/         # Custom ASGI middlewares (audit logging, timing)
│   ├── model/              # SQLAlchemy 2.0 ORM domain entities
│   ├── repository/         # Generic async CRUD repositories (BaseRepository)
│   ├── service/            # Business logic & transaction boundaries
│   ├── util/               # Helper utilities (datetime, timezone, timezone parsing)
│   └── main.py             # FastAPI application entrypoint & lifespan
├── scripts/                # Utility scripts (check_db, seed)
├── tests/                  # Pytest test suite (unit & integration)
└── pyproject.toml          # uv package definition & dependencies
```

---

## Tech Stack & Component Responsibilities

The backend tech stack is selected for high asynchronous throughput, enterprise-grade data integrity, flexible multi-provider AI reasoning, and strict accountability.

### 1. Web Framework & Asynchronous Core

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **Python** | `>=3.12, <3.14` | Modern Python runtime leveraging PEP 695 type parameter syntax, enhanced async event loops, and performance optimizations. |
| **FastAPI** | `^0.141.0` | Asynchronous ASGI web framework. Exposes HTTP REST endpoints, validates inputs via Pydantic, handles dependency injection (`get_db`, `get_current_user`), and generates OpenAPI/Swagger schemas at `/docs`. |
| **Uvicorn** | `^0.32.0` | Lightning-fast ASGI web server with auto-reload capabilities for local development. |

### 2. Database, ORM & Persistence

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **SQLAlchemy 2.0 (AsyncIO)** | `^2.0.36` | Asynchronous Object-Relational Mapper. Uses Declarative Base (`BaseModel`) with UUID primary keys and timestamp tracking for all domain tables (`Contact`, `CandidateApplication`, `CalendarEvent`, `ActionPlan`, `AuditLog`). |
| **asyncpg** | `^0.30.0` | High-performance asynchronous PostgreSQL database driver used for all application CRUD operations and connection pooling. |
| **psycopg 3 (binary, pool)** | `^3.2.0` | Modern PostgreSQL driver providing connection pooling for synchronous workloads, specifically tailored for the LangGraph PostgreSQL checkpointer. |
| **pgvector** | `^0.3.6` | Vector similarity extension for PostgreSQL. Enables semantic search and contextual RAG over company policies, job criteria, and candidate notes. |
| **Alembic** | `^1.14.0` | Database schema migration management. Automatically detects changes in SQLAlchemy declarative models to generate reproducible schema versions (`alembic upgrade head`). |

### 3. Data Validation & Configuration

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **Pydantic v2** | `^2.10.0` | Rust-backed data validation and serialization library. Powers all DTOs (`BaseDTO`, `ApiResponse[T]`), guaranteeing strict request payload checking and response formatting. |
| **Pydantic Settings** | `^2.6.0` | Type-safe environment variable parsing. Reads directly from the shared monorepo root `.env` (`Settings` in `app/core/config.py`). |

### 4. Security & Cryptography

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **PyJWT** | `^2.10.0` | JSON Web Token encoding and decoding for stateless user authentication and session verification. |
| **pwdlib [argon2]** | `^0.2.1` | State-of-the-art password hashing using the Argon2id algorithm, protecting user credentials against brute-force and GPU-accelerated attacks. |

### 5. AI Orchestration, Agents & Observability

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **LangChain Core & Community** | `^0.3.0` | Foundational abstractions for prompt templates, chat message schemas (`HumanMessage`, `AIMessage`), tools, and generic model invocation. |
| **Multi-Provider Connectors** | | Connectors enabling runtime model switching and fallback: |
| • `langchain-google-genai` | `^2.0.0` | Official Google Gemini integration (e.g. Gemini 2.0 Flash / Pro) for triage reasoning. |
| • `langchain-openai` | `^0.2.0` | OpenAI integration (GPT-4o, GPT-4o-mini). |
| • `langchain-anthropic` | `^0.3.0` | Anthropic Claude integration (Claude 3.5 Sonnet). |
| • `langchain-groq` | `^0.2.0` | Groq ultra-fast LPU inference (Llama 3 / Mixtral) for low-latency screening. |
| • `langchain-ollama` | `^0.2.0` | Local offline LLM runner for data-sensitive or on-premise deployments. |
| **LangGraph** | `^0.2.0` | **Primary Top-Level Orchestrator**. Implements cyclic state graphs for multi-agent triage: Guardrail Scanner → Context Retriever → Planner Agent → Secondary Validator → Human Approval Gate (`interrupt_before`) → 60s Undo Buffer → Executor → Audit Logger. |
| **LangGraph Checkpoint Postgres** | `^2.0.0` | Durable state checkpointer. Stores agent conversation state, pending approvals, and execution history directly in PostgreSQL. |
| **LangSmith** | `^0.1.0` | Production LLM observability platform. Traces every LLM call, token usage, latency, and agent branch execution for transparent monitoring and evaluation. |
| **Google ADK (`google-adk`)** | `^2.12.0` | **Experimental Sub-Agent**. Strictly isolated in `app/agent/adk/` behind the `ENABLE_EXPERIMENTAL_ADK_AGENT` feature flag, reserved for exploring Gemini-native capabilities. |

### 6. Development, Linting & Testing

| Technology | Version | Purpose & Functionality in Heketon |
| :--- | :--- | :--- |
| **uv** | `Latest` | Extremely fast package manager and virtual environment tool built in Rust. Replaces pip, poetry, and virtualenv. |
| **Pytest & Pytest-Asyncio** | `^8.3.0` / `^0.24.0` | Unit and integration test suite runner with native asynchronous test execution. |
| **Httpx** | `^0.28.0` | Async HTTP client used by tests (`AsyncClient`) to verify FastAPI endpoints without starting a live socket. |
| **Ruff** | `^0.8.0` | Blazing-fast Python linter and code formatter. Enforces style guides and best practices. |

---

## Environment Configuration

Backend configuration is loaded from the **shared monorepo root `.env`** (`Heketon/.env`). Key variables include:

```ini
# Application
PROJECT_NAME="Heketon API"
API_V1_STR="/api/v1"
ENVIRONMENT="development"
DEBUG=true
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]

# Database & Checkpointer
DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/postgres"
LANGGRAPH_CHECKPOINT_DB_URI="postgresql://postgres:postgres@localhost:5432/postgres"

# AI & Observability
OPENAI_API_KEY=""
GOOGLE_API_KEY=""
ANTHROPIC_API_KEY=""
GROQ_API_KEY=""
OLLAMA_BASE_URL="http://localhost:11434"

# LangSmith Tracing
LANGSMITH_TRACING=false
LANGSMITH_API_KEY=""
LANGSMITH_PROJECT="heketon-agent"
LANGSMITH_ENDPOINT="https://api.smith.langchain.com"

# Feature Flags
ENABLE_EXPERIMENTAL_ADK_AGENT=false
```

---

## Developer Commands

Run from the `backend/` directory:

```bash
# Install / synchronize dependencies
uv sync

# Run development server with live reload
uv run fastapi dev app/main.py

# Run test suite
uv run pytest

# Run linter & formatter check
uv run ruff check .
uv run ruff check --fix .

# Verify database connection and pgvector extension
uv run python -m scripts.check_db

# Alembic migrations
uv run alembic revision --autogenerate -m "migration_description"
uv run alembic upgrade head
```
