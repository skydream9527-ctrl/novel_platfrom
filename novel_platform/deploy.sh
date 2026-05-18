#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Novel Platform Deploy ==="

# Check prerequisites
command -v python3 >/dev/null || { echo "ERROR: python3 not found"; exit 1; }
command -v node >/dev/null || { echo "ERROR: node not found"; exit 1; }
command -v npm >/dev/null || { echo "ERROR: npm not found"; exit 1; }

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python: $PYTHON_VERSION"
echo "Node: $(node --version)"

# Copy .env if missing
[ -f .env ] || cp .env.example .env

# Backend
echo ""
echo "--- Backend ---"
cd backend
if [ ! -d .venv ]; then
    python3 -m venv .venv
fi
. .venv/bin/activate
pip install -e ".[dev]" -q
echo "Backend installed."
cd ..

# Frontend
echo ""
echo "--- Frontend ---"
cd frontend
if [ ! -d node_modules ]; then
    npm install
fi
echo "Frontend installed."
cd ..

MODE="${1:-}"

if [ "$MODE" = "--run" ]; then
    echo ""
    echo "=== Starting dev servers ==="
    echo "Frontend: http://localhost:5173"
    echo "Backend:  http://localhost:8000"
    echo ""
    cd backend && . .venv/bin/activate && uvicorn app.main:app --reload --port 8000 &
    cd frontend && npm run dev &
    wait
elif [ "$MODE" = "--prod" ]; then
    echo ""
    echo "=== Building frontend ==="
    cd frontend && npm run build && cd ..
    echo ""
    echo "=== Starting production server ==="
    echo "Access at: http://0.0.0.0:8000"
    cd backend && . .venv/bin/activate && uvicorn app.main:app --host 0.0.0.0 --port 8000
else
    echo ""
    echo "Install complete. Run with:"
    echo "  ./deploy.sh --run    (dev mode)"
    echo "  ./deploy.sh --prod   (production)"
fi
