# Heketon Backend

FastAPI backend using layered MVC conventions (`model`, `dto`, `repository`, `service`, `controller`, `agent`), Async SQLAlchemy 2.0 + Alembic, and LangChain / LangGraph managed with `uv`.

Reads environment variables directly from the **shared monorepo root `.env`** (`../.env`).

## Quick Start

```bash
# Install dependencies
uv sync

# Run dev server
uv run fastapi dev app/main.py

# Run tests & linter
uv run pytest
uv run ruff check .

# Check external PostgreSQL / Supabase connection
uv run python -m scripts.check_db

# Generate & apply Alembic migrations
uv run alembic revision --autogenerate -m "init"
uv run alembic upgrade head
```
