#!/usr/bin/env bash
set -e

echo "========================================================"
echo "🚀 Starting Heketon Unified Service (FastAPI + Next.js)"
echo "   Node.js: $(node -v)"
echo "   Python:  $(python3 --version)"
echo "========================================================"

# Optional automatic database migration
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "📦 [Migration] Executing Alembic database migrations..."
    (cd /app/backend && python3 -m alembic upgrade head) || {
        echo "❌ [Migration] Failed to run database migrations, exiting."
        exit 1
    }
    echo "✅ [Migration] Database migrations completed."
fi

# 1. Start FastAPI Backend in background
echo "⚡ Starting FastAPI Backend on 0.0.0.0:8000..."
cd /app/backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
echo "✅ Backend started with PID: $BACKEND_PID"

# 2. Start Next.js Frontend in background
echo "🌐 Starting Next.js Frontend on 0.0.0.0:3000..."
cd /app/frontend
node server.js &
FRONTEND_PID=$!
echo "✅ Frontend started with PID: $FRONTEND_PID"

# 3. Graceful shutdown handler
shutdown() {
    echo "🛑 Received shutdown signal. Terminating child processes gracefully..."
    kill -TERM "$FRONTEND_PID" 2>/dev/null || true
    kill -TERM "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    wait "$BACKEND_PID" 2>/dev/null || true
    echo "👋 Heketon Unified processes stopped cleanly."
    exit 0
}

trap shutdown SIGTERM SIGINT SIGHUP

# 4. Wait for any child process to terminate
set +e
wait -n "$BACKEND_PID" "$FRONTEND_PID"
EXIT_CODE=$?
set -e

echo "⚠️ A core service exited with code $EXIT_CODE. Shutting down container..."
kill -TERM "$FRONTEND_PID" 2>/dev/null || true
kill -TERM "$BACKEND_PID" 2>/dev/null || true
exit $EXIT_CODE
