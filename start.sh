#!/usr/bin/env bash
# =============================================================================
# start.sh — launch the backend (Django) and frontend (Vite) together
# =============================================================================
# Usage:
#   ./start.sh            # starts both backend and frontend
#   ./start.sh backend    # starts only Django on port 8001
#   ./start.sh frontend   # starts only Vite on port 5173
# =============================================================================

set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

log()  { echo -e "${GREEN}[start.sh]${NC} $*"; }
warn() { echo -e "${YELLOW}[start.sh]${NC} $*"; }
err()  { echo -e "${RED}[start.sh]${NC} $*"; }

# ---------------------------------------------------------------------------
start_backend() {
    log "Starting Django backend on port 8001..."
    cd "$BACKEND"

    # Activate venv if present
    if [ -f "venv/bin/activate" ]; then
        # shellcheck disable=SC1091
        source venv/bin/activate
        log "  Activated venv"
    else
        warn "  No venv found — using system Python. Run 'python -m venv venv && pip install -r requirements.txt' first."
    fi

    if [ ! -f ".env" ]; then
        warn "  backend/.env not found — copying from .env.example"
        cp .env.example .env
    fi

    # Run migrations (non-destructive)
    python manage.py migrate --run-syncdb --noinput 2>&1 | tail -5

    log "  Django running at http://localhost:8001"
    log "  Health check: http://localhost:8001/api/health/"
    DJANGO_SETTINGS_MODULE=core.settings python manage.py runserver 8001
}

# ---------------------------------------------------------------------------
start_frontend() {
    log "Starting Vite frontend on port 5173..."
    cd "$FRONTEND"

    if [ ! -d "node_modules" ]; then
        log "  node_modules not found — running npm install..."
        npm install
    fi

    log "  Vite dev server: http://localhost:5173"
    log "  API proxy: /api  →  http://localhost:8001"
    npm run dev
}

# ---------------------------------------------------------------------------
MODE="${1:-both}"

case "$MODE" in
  backend)
    start_backend
    ;;
  frontend)
    start_frontend
    ;;
  both|*)
    log "Starting both services..."
    log "  Backend → http://localhost:8001"
    log "  Frontend → http://localhost:5173"
    echo ""

    trap 'echo; log "Shutting down..."; kill %1 %2 2>/dev/null; exit 0' SIGINT SIGTERM

    # Start backend in background
    (
        cd "$BACKEND"
        [ -f "venv/bin/activate" ] && source venv/bin/activate
        [ ! -f ".env" ] && cp .env.example .env
        python manage.py migrate --run-syncdb --noinput >/dev/null 2>&1
        DJANGO_SETTINGS_MODULE=core.settings python manage.py runserver 8001
    ) 2>&1 | sed 's/^/[backend] /' &

    # Give Django a moment to boot
    sleep 3

    # Start frontend in background
    (
        cd "$FRONTEND"
        [ ! -d "node_modules" ] && npm install >/dev/null 2>&1
        npm run dev
    ) 2>&1 | sed 's/^/[frontend] /' &

    log "Both services started. Press Ctrl+C to stop."
    wait
    ;;
esac
