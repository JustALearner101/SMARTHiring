# ==============================================================================
# Heketon - Unified Multistage Container (Next.js 16 + FastAPI 0.115 + LangGraph)
# Production-ready, non-root, dual-process container orchestrated via tini.
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1A: Frontend Dependencies Cache
# ------------------------------------------------------------------------------
FROM node:22-bookworm-slim AS frontend-deps
WORKDIR /build/frontend

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY frontend/package.json frontend/pnpm-lock.yaml ./
RUN pnpm install --frozen-lockfile

# ------------------------------------------------------------------------------
# Stage 1B: Frontend Standalone Build
# ------------------------------------------------------------------------------
FROM node:22-bookworm-slim AS frontend-builder
WORKDIR /build/frontend

RUN corepack enable && corepack prepare pnpm@latest --activate

COPY --from=frontend-deps /build/frontend/node_modules ./node_modules
COPY frontend/ ./

ARG NEXT_PUBLIC_APP_NAME="Heketon"
ARG NEXT_PUBLIC_API_URL="/api/v1"
ARG NEXT_PUBLIC_SUPABASE_URL=""
ARG NEXT_PUBLIC_SUPABASE_ANON_KEY=""

ENV NEXT_PUBLIC_APP_NAME=$NEXT_PUBLIC_APP_NAME \
    NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL \
    NEXT_PUBLIC_SUPABASE_URL=$NEXT_PUBLIC_SUPABASE_URL \
    NEXT_PUBLIC_SUPABASE_ANON_KEY=$NEXT_PUBLIC_SUPABASE_ANON_KEY \
    NEXT_TELEMETRY_DISABLED=1

RUN pnpm build

# ------------------------------------------------------------------------------
# Stage 2: Backend Virtual Environment Build (Astral uv)
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS backend-builder
WORKDIR /build/backend

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY backend/ ./
RUN uv sync --frozen --no-dev

# ------------------------------------------------------------------------------
# Stage 3: Unified Production Runner (Debian Bookworm Slim)
# ------------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runner
WORKDIR /app

# 1. Install system utilities: tini (PID 1 supervisor) and curl (healthcheck)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tini \
        curl \
        ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# 2. Copy official Node.js 22 runtime binary and libraries from Node bookworm image
COPY --from=node:22-bookworm-slim /usr/local/bin/node /usr/local/bin/node
COPY --from=node:22-bookworm-slim /usr/local/lib/node_modules /usr/local/lib/node_modules

# 3. Create non-root dedicated security user
RUN groupadd -g 1001 heketon && \
    useradd -u 1001 -g heketon -m -s /bin/bash heketon

# 4. Copy Backend application, virtualenv, and config
COPY --from=backend-builder --chown=heketon:heketon /build/backend/.venv /app/backend/.venv
COPY --from=backend-builder --chown=heketon:heketon /build/backend/app /app/backend/app
COPY --from=backend-builder --chown=heketon:heketon /build/backend/alembic /app/backend/alembic
COPY --from=backend-builder --chown=heketon:heketon /build/backend/alembic.ini /app/backend/alembic.ini
COPY --from=backend-builder --chown=heketon:heketon /build/backend/scripts /app/backend/scripts
RUN mkdir -p /app/backend/storage && chown -R heketon:heketon /app/backend/storage

# 5. Copy Frontend standalone build, static assets, and public directory
COPY --from=frontend-builder --chown=heketon:heketon /build/frontend/public /app/frontend/public
COPY --from=frontend-builder --chown=heketon:heketon /build/frontend/.next/standalone /app/frontend
COPY --from=frontend-builder --chown=heketon:heketon /build/frontend/.next/static /app/frontend/.next/static

# 6. Copy Entrypoint supervisor script
COPY --chown=heketon:heketon scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Environment settings
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0" \
    PYTHONUNBUFFERED=1 \
    PATH="/app/backend/.venv/bin:$PATH"

# Switch to non-root user
USER heketon

# Expose Next.js Web UI (:3000) and FastAPI Backend / MCP (:8000)
EXPOSE 3000 8000

# Native Docker Healthcheck targeting FastAPI health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Launch with tini as PID 1 to ensure proper signal propagation and zombie reaping
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/app/scripts/docker-entrypoint.sh"]
