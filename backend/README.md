# Heketon Backend

FastAPI asynchronous backend for **Heketon** (HR & Office Ops AI Orchestrator), built for the Tencent Cloud Hackathon Indonesia 2026. The backend autonomously orchestrates interview schedule triage, multi-agent candidate evaluation, conflict resolution, and human-in-the-loop approvals across WhatsApp and Email.

---

## Technical Documentation Suite

Detailed architectural, contract, database, and testing documentation is organized in `docs/backend/`:

- [**Architecture & File Structure Specification**](../docs/backend/ARCHITECTURE_AND_STRUCTURE.md): Detailed layer breakdown, Single Responsibility Principle (SRP), CamelCase/PascalCase naming standards, and dependency flow.
- [**API Contracts & OpenAPI Specification**](../docs/backend/API_CONTRACTS.md): Full OpenAPI catalog covering all 16 endpoint domains, standard `ApiResponse[T]` envelope, pagination contracts, and sample JSON payloads.
- [**Database & Migrations Guide**](../docs/backend/DATABASE_AND_MIGRATIONS.md): PostgreSQL + `pgvector` relational schema, check constraints, Alembic migration workflows, and development data seeding.
- [**Testing & Quality Assurance Guide**](../docs/backend/TESTING_AND_DEVELOPMENT.md): Pytest architecture, async fixtures lifecycle in `conftest.py`, Ruff linter setup, and execution commands.

---

## Architecture Overview

The backend uses a strict **Layered Architecture** under `app/`. Dependencies strictly flow unidirectionally:

$$\text{Controller (HTTP)} \longrightarrow \text{Service (Logic)} \longrightarrow \text{Repository (Data Access)} \longrightarrow \text{Model (SQLAlchemy)}$$

```
backend/
├── alembic/                          # Alembic schema migrations (PostgreSQL)
│   └── versions/                     # Migration scripts (current: 06784f3e4d33)
├── app/
│   ├── controller/                   # 16 Standalone CamelCase Routers (/api/v1/...)
│   │   ├── ActionPlanController.py
│   │   ├── AuditLogController.py
│   │   ├── CalendarMatrixController.py
│   │   ├── CandidateController.py
│   │   ├── ContactController.py
│   │   ├── HolidayController.py
│   │   ├── InterviewDecisionController.py
│   │   ├── InterviewSessionController.py
│   │   ├── InterviewTranscriptController.py
│   │   ├── NegotiationThreadController.py
│   │   ├── OperationalPolicyController.py
│   │   ├── OrchestratorCommandController.py
│   │   ├── RubricController.py
│   │   ├── SimulatorEmailController.py
│   │   ├── SimulatorWhatsAppController.py
│   │   └── SlotConflictCheckerController.py
│   ├── service/                      # 16 Standalone CamelCase Business Services
│   │   ├── ActionPlanService.py
│   │   ├── AuditLogService.py
│   │   ├── CandidateService.py
│   │   └── ... (13 more domain services)
│   ├── repository/                   # 12 Standalone CamelCase Repositories
│   │   ├── BaseRepository.py         # Generic CRUD repository (PEP 695 generics)
│   │   ├── CandidateRepository.py
│   │   └── ... (11 domain repositories)
│   ├── dto/                          # 16 Standalone CamelCase Pydantic DTOs
│   │   ├── BaseDTO.py                # ApiResponse, PaginatedResponse, PaginationParams
│   │   ├── CandidateDTO.py
│   │   └── ... (14 domain DTOs)
│   ├── model/                        # 11 CamelCase SQLAlchemy 2.0 ORM Entities
│   │   ├── BaseModel.py              # Base declarative, TableBaseModel, AppendOnlyBaseModel
│   │   ├── AuditModel.py
│   │   ├── CalendarModel.py
│   │   ├── CandidateModel.py
│   │   ├── FollowupModel.py
│   │   ├── InterviewModel.py
│   │   ├── JobModel.py
│   │   ├── OrchestrationModel.py
│   │   ├── RubricModel.py
│   │   ├── SummaryModel.py
│   │   └── UserModel.py
│   ├── exception/                    # Exception Handling Architecture
│   │   ├── CustomException.py        # AppException, NotFoundException, ConflictException
│   │   └── ExceptionHandler.py       # Global FastAPI exception handlers
│   ├── core/                         # Configuration & Security Utilities
│   │   ├── AppConfig.py              # Pydantic Settings loading shared root .env
│   │   └── AppSecurity.py            # Argon2 password hashing & JWT utilities
│   ├── db/                           # Async Database Engine & Session Provider
│   │   └── DatabaseSession.py        # engine, AsyncSessionLocal, get_db dependency
│   ├── constant/                     # Application enums & constants
│   ├── middleware/                   # ASGI middleware (CORS, timing, audit)
│   ├── util/                         # Timezone & date helpers
│   └── main.py                       # FastAPI entry point & lifespan
├── scripts/                          # Utility scripts (check_db, seed)
├── tests/                            # Pytest test suite (36 tests passing)
│   ├── unit/                         # Unit tests (DTOs, Rules, Handlers, Pagination)
│   └── integration/                  # Comprehensive API endpoint integration tests
└── pyproject.toml                    # uv package definition & dependencies
```

---

## 16 Modular Controller Domains

All 16 controllers are mounted under `/api/v1` and cataloged in Swagger UI (`/docs`):

| Domain Tag | Base Route | Controller File | Primary Responsibility |
| :--- | :--- | :--- | :--- |
| **CandidateManagement** | `/api/v1/candidates` | `CandidateController.py` | ATS candidate profiles, codes, & application status. |
| **ContactsDirectory** | `/api/v1/contacts` | `ContactController.py` | Interviewer profiles, departments, & working hours. |
| **NationalHolidays** | `/api/v1/holidays` | `HolidayController.py` | National holiday & cuti bersama calendar. |
| **OperationalPolicies** | `/api/v1/operationalRules` | `OperationalPolicyController.py` | Office working hours, buffers, & Friday prayer rules. |
| **AssessmentRubrics** | `/api/v1/rubrics` | `RubricController.py` | Position competencies & evaluation rubrics. |
| **OrchestratorCommands** | `/api/v1/orchestrator` | `OrchestratorCommandController.py` | NL command triage dispatch & preset scenarios. |
| **ActionPlans** | `/api/v1/actionPlans` | `ActionPlanController.py` | Interview action plans, human approval, & 60s undo. |
| **NegotiationThreads** | `/api/v1/negotiationThreads` | `NegotiationThreadController.py` | Cross-platform scheduling conversation threads. |
| **SimulatorEmail** | `/api/v1/simulator/email` | `SimulatorEmailController.py` | Webmail simulator for interviewer invitations. |
| **SimulatorWhatsApp** | `/api/v1/simulator/whatsapp` | `SimulatorWhatsAppController.py` | WhatsApp chat simulator & quick candidate presets. |
| **InterviewSessions** | `/api/v1/interviews/sessions` | `InterviewSessionController.py` | Interview audio uploads, consent, & session status. |
| **InterviewTranscripts** | `/api/v1/interviews/transcripts` | `InterviewTranscriptController.py` | Audio transcription segments & confidence scores. |
| **InterviewDecisions** | `/api/v1/interviews/decisions` | `InterviewDecisionController.py` | Final HR decision gates (ADVANCE / HOLD / REJECT). |
| **CalendarMatrix** | `/api/v1/calendarMatrix` | `CalendarMatrixController.py` | Aggregated interviewer availability matrix. |
| **SlotConflictChecker** | `/api/v1/slotConflictChecker` | `SlotConflictCheckerController.py` | Pre-flight conflict & Friday prayer blackout check. |
| **AuditLogs** | `/api/v1/auditLogs` | `AuditLogController.py` | SHA-256 hash-chained immutable audit ledger. |

---

## Tech Stack

| Component | Library / Tool | Version | Role in Heketon |
| :--- | :--- | :--- | :--- |
| **Runtime** | Python | `>=3.12, <3.14` | Modern async Python with PEP 695 generics. |
| **Web Framework** | FastAPI | `^0.141.0` | High-performance asynchronous REST API framework. |
| **ASGI Server** | Uvicorn | `^0.32.0` | Development server with hot-reload. |
| **ORM** | SQLAlchemy 2.0 | `^2.0.36` | Asynchronous ORM with Declarative Models. |
| **Database Driver** | asyncpg | `^0.30.0` | Async driver for PostgreSQL application CRUD. |
| **Sync Driver** | psycopg 3 | `^3.2.0` | Synchronous driver for LangGraph PostgreSQL checkpointer. |
| **Vector DB** | pgvector | `^0.3.6` | Vector similarity extension for semantic searches. |
| **Migrations** | Alembic | `^1.14.0` | Database schema migrations (`alembic upgrade head`). |
| **Validation** | Pydantic v2 | `^2.10.0` | Strict data validation & schema contracts. |
| **Security** | PyJWT & pwdlib [argon2] | `^2.10.0` / `^0.2.1` | JWT stateless auth & Argon2id password hashing. |
| **Package Manager** | uv | `Latest` | Blazing-fast Rust-based Python package manager. |
| **Testing** | Pytest, Httpx, AnyIO | Latest | Comprehensive test suite (36 tests passing). |
| **Linter / Formatter**| Ruff | `^0.8.0` | Ultra-fast linter with CamelCase module support. |

---

## Developer Commands

Run from `backend/`:

```bash
# 1. Synchronize virtual environment dependencies
uv sync

# 2. Run local FastAPI development server (reload mode)
uv run fastapi dev app/main.py

# 3. Run full test suite (unit + integration tests)
uv run pytest

# 4. Run linter check
uv run ruff check .

# 5. Automatically fix linting and import issues
uv run ruff check --fix .

# 6. Verify database connectivity & pgvector extension
uv run python -m scripts.check_db

# 7. Seed initial development data
uv run python -m scripts.seed

# 8. Unseed / purge development data (--keep-admin / --all / --dry-run)
uv run python -m scripts.unseed

# 8. Apply Alembic migrations
uv run alembic upgrade head
```
