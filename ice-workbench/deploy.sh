#!/usr/bin/env bash
# ICE Workbench — one-shot deploy script. Works on macOS + Linux.
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh              # 只安装依赖（含 pytest）
#   ./deploy.sh --run        # 安装后用 dev 模式起（:5173 + :8000）
#   ./deploy.sh --prod       # 安装后用生产模式起：构建前端 + 后端单端口监听 0.0.0.0
#
# Environment:
#   ICE_BIND_PORT   生产监听端口（默认 8000）
#   ICE_BIND_HOST   生产绑定地址（默认 0.0.0.0，公网可达）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

# ---- color logging ----
GREEN=$'\033[32m'
YELLOW=$'\033[33m'
RED=$'\033[31m'
RESET=$'\033[0m'
ok() { printf "%s✓%s %s\n" "$GREEN" "$RESET" "$*"; }
warn() { printf "%s!%s %s\n" "$YELLOW" "$RESET" "$*"; }
err() { printf "%s✗%s %s\n" "$RED" "$RESET" "$*"; exit 1; }
section() { printf "\n%s── %s ──%s\n" "$YELLOW" "$*" "$RESET"; }

MODE="${1:-install}"
BIND_PORT="${ICE_BIND_PORT:-8000}"
BIND_HOST="${ICE_BIND_HOST:-0.0.0.0}"

# ---- 1. environment checks ----
section "Environment"
uname_s=$(uname -s 2>/dev/null || echo unknown)
ok "OS: $uname_s"

command -v python3 >/dev/null 2>&1 || err "python3 not found. Install Python 3.10+ first."
PY_VER=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PY_MAJOR=$(python3 -c 'import sys; print(sys.version_info.major)')
PY_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
  err "Python $PY_VER is too old. Need Python 3.10 or newer."
fi
ok "Python $PY_VER"

command -v node >/dev/null 2>&1 || err "node not found. Install Node 18+ (https://nodejs.org/)."
NODE_VER=$(node --version)
NODE_MAJOR=$(node --version | sed 's/^v\([0-9]*\)\..*/\1/')
if [ "$NODE_MAJOR" -lt 18 ]; then
  err "Node $NODE_VER is too old. Need Node 18 or newer."
fi
ok "Node $NODE_VER"

command -v npm >/dev/null 2>&1 || err "npm not found. Should ship with Node."
ok "npm $(npm --version)"

# Optional tools — warn but don't block
if ! command -v kyuubi >/dev/null 2>&1; then
  warn "kyuubi CLI not found — SQL 查询工具会返回 KYUUBI_NOT_CONFIGURED。Linux 安装：pipx install xiaomi-kyuubi-cli"
fi
if ! command -v feishu >/dev/null 2>&1; then
  warn "feishu CLI not found — 发布到飞书会返回 FEISHU_CLI_NOT_INSTALLED。按内部文档安装 feishu CLI 后可用。"
fi

if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
    warn ".env not found — copied from .env.example. Edit it to set your keys."
  else
    err "Neither .env nor .env.example present in $ROOT."
  fi
else
  ok ".env present"
fi

# ---- 2. backend ----
section "Backend (FastAPI)"
cd backend
if [ ! -d .venv ]; then
  python3 -m venv .venv
  ok "Created backend/.venv"
fi
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip --quiet
ok "pip $(python -m pip --version | awk '{print $2}')"

python -m pip install -e ".[dev]" --quiet
ok "Backend dependencies installed"

python -c "from app.main import app; n=len([r for r in app.routes if hasattr(r,'path')]); print(f'  → {n} routes registered')"
if python -m pytest -q --no-header 2>&1 | tail -1 | grep -q "passed"; then
  ok "Backend tests passed"
else
  warn "Backend tests reported failures — review manually"
fi
deactivate
cd "$ROOT"

# ---- 3. frontend ----
section "Frontend (React + Vite)"
cd frontend
if [ ! -d node_modules ]; then
  npm install --no-audit --no-fund
  ok "Installed node_modules"
else
  npm install --no-audit --no-fund --silent
  ok "node_modules up-to-date"
fi
npx tsc --noEmit && ok "Frontend typecheck clean"
cd "$ROOT"

# ---- 4. mode-specific action ----
section "Ready"

cat <<EOF

  ${GREEN}Setup complete.${RESET}

  Default account:
    user: ${YELLOW}admin${RESET}
    pass: ${YELLOW}admin123${RESET}  ${YELLOW}(生产环境首次登录请修改)${RESET}

EOF

if [ "$MODE" = "--prod" ]; then
  if [ -f frontend/dist/index.html ]; then
    ok "frontend/dist/ already built — skipping rebuild"
  else
    section "Building frontend dist"
    cd frontend && npm run build && cd "$ROOT"
    ok "frontend/dist/ built"
  fi

  section "Starting production server on $BIND_HOST:$BIND_PORT"
  cat <<EOF

  单端口部署 — 同端口同时伺服 SPA + API + WebSocket。
  浏览器访问： ${YELLOW}http://<服务器 IP>:$BIND_PORT${RESET}
  健康检查：   ${YELLOW}http://<服务器 IP>:$BIND_PORT/api/v1/health${RESET}

  公网可达检查清单：
    1. 防火墙放行：   ${YELLOW}sudo ufw allow $BIND_PORT${RESET}（Debian/Ubuntu）或 firewalld
    2. 云服务器安全组 / VPC 开放 TCP $BIND_PORT 入站
    3. 内网穿透 / 反向代理（nginx + https 可选）

EOF
  cd backend && source .venv/bin/activate
  exec uvicorn app.main:app --host "$BIND_HOST" --port "$BIND_PORT" --workers 1
elif [ "$MODE" = "--run" ]; then
  section "Starting dev servers"
  exec make dev
else
  cat <<EOF
  继续：
    ${YELLOW}./deploy.sh --prod${RESET}  # 生产单端口（公网可访问）
    ${YELLOW}./deploy.sh --run${RESET}   # dev 模式（前端 :5173 + 后端 :8000）
    ${YELLOW}make dev${RESET}            # 同上
    ${YELLOW}make prod${RESET}           # 同 --prod

EOF
fi
