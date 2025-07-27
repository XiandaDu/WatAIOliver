#!/usr/bin/env bash
# setup.sh — macOS/Linux helper for Oliver project
# - Conda env: oliver3.12.2 (Python 3.12.2)
# - Default: setup + run backend/pdf/rag/agent + frontend
# - .env policy: never clear/overwrite existing keys; only prompt for GEMINI/CEREBRAS if empty/<...>;
#   create .env if missing with Supabase defaults; warn if existing Supabase differs; proceed with user's values.

set -Eeuo pipefail

#############################################
# Global config
#############################################
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$ROOT_DIR/.env"
LOG_DIR="$ROOT_DIR/logs"
PID_DIR="$ROOT_DIR/.pids"

PY_VERSION="3.12.2"
CONDA_ENV="oliver3.12.2"
DEFAULT_MINICONDA_PREFIX="$HOME/miniconda3"

BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
ML_DIR="$ROOT_DIR/machine_learning"
PDF_PROC_DIR="$ML_DIR/pdf_processor"
RAG_DIR="$ML_DIR/rag_system"
AGENT_DIR="$ML_DIR/ai_agents"

# Services & ports
BACKEND_PORT=8000
PDF_PORT=8001
RAG_PORT=8002
AGENT_PORT=8003

# Project-default Supabase (do not auto-overwrite an existing .env)
DEFAULT_SUPABASE_URL="https://zeyggksxsfrqziseysnr.supabase.co"
DEFAULT_SUPABASE_SERVICE_ROLE_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InpleWdna3N4c2ZycXppc2V5c25yIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0OTg1OTU1NiwiZXhwIjoyMDY1NDM1NTU2fQ.RNiZ2p_mVMwztyBhUea39iphKw7VatjS6VXu_VGkHuo"

# Colors
t_reset="\033[0m"; t_red="\033[31m"; t_green="\033[32m"; t_yellow="\033[33m"; t_blue="\033[34m"; t_cyan="\033[36m"

#############################################
# Utility
#############################################
die() { echo -e "${t_red}Error:${t_reset} $*" >&2; exit 1; }
warn() { echo -e "${t_yellow}Warning:${t_reset} $*" >&2; }
info() { echo -e "${t_cyan}$*${t_reset}"; }
ok() { echo -e "${t_green}$*${t_reset}"; }

ensure_dirs() { mkdir -p "$LOG_DIR" "$PID_DIR"; }

# Robustly read KEY's value from .env:
# - ignores commented lines
# - allows optional leading spaces, optional 'export', and spaces around '='
get_env_var() {
  local key="$1"
  [[ -f "$ENV_FILE" ]] || return 0
  # First non-comment match; allow optional "export" prefix
  local line
  line="$(grep -E -m1 "^[[:space:]]*(export[[:space:]]+)?${key}[[:space:]]*=" "$ENV_FILE" || true)"
  [[ -n "${line:-}" ]] || return 0
  # Strip trailing inline comment and extract value
  line="${line%%#*}"
  line="${line#*=}"
  # Trim spaces and CR
  line="${line%"${line##*[!$'\r' ]}"}"
  line="${line#"${line%%[!$'\r' ]*}"}"
  printf '%s' "$line"
}

# Set/replace KEY=value in .env (idempotent, portable), tolerant of spaces/export.
# - Replaces the first active occurrence of KEY=... (ignoring comments)
# - If not present, appends KEY=value
# - Never touches other keys
set_env_var() {
  local key="$1" value="$2" tmp
  tmp="$(mktemp)"
  touch "$ENV_FILE"
  awk -v K="$key" -v V="$value" '
    BEGIN{done=0}
    {
      # If this is a comment line, just print it
      if ($0 ~ /^[[:space:]]*#/) { print; next }
      # Match optional leading spaces, optional "export", key, optional spaces, equals
      if (!done && $0 ~ "^[[:space:]]*(export[[:space:]]+)?[[:space:]]*"K"[[:space:]]*=") {
        print K"="V
        done=1
        next
      }
      print
    }
    END{
      if (!done) print K"="V
    }
  ' "$ENV_FILE" > "$tmp"
  mv "$tmp" "$ENV_FILE"
}

# Trim leading/trailing spaces and CR from a variable (in-place via echo)
trim_val() {
  local s="$1"
  # Remove trailing CR (from possible Windows paste)
  s="${s%$'\r'}"
  # Trim leading/trailing whitespace
  s="${s#"${s%%[!$'\t \r\n']*}"}"
  s="${s%"${s##*[!$'\t \r\n']}"}"
  printf '%s' "$s"
}

# Return 0 if value is empty or placeholder like <...> (quotes are allowed)
# Return 0 (true) if value is empty or looks like a placeholder <...>
# Return 0 (true) if value is empty or looks like a placeholder <...>
is_empty_or_placeholder() {
  local val
  val="$(trim_val "${1:-}")"

  # Strip surrounding quotes if present
  if [[ "${val:0:1}" == "\"" && "${val: -1}" == "\"" ]]; then
    val="${val:1:${#val}-2}"
  elif [[ "${val:0:1}" == "'" && "${val: -1}" == "'" ]]; then
    val="${val:1:${#val}-2}"
  fi

  # Empty?
  [[ -z "$val" ]] && return 0

  # Placeholder like <...> — use plain string tests (no regex)
  if [[ "${val:0:1}" == "<" && "${val: -1}" == ">" ]]; then
    return 0
  fi

  return 1
}

prompt_secret_required() {
  # $1=KEY, $2=help text
  local key="$1" help="$2" cur
  cur="$(get_env_var "$key" || true)"
  if is_empty_or_placeholder "${cur:-}"; then
    echo
    info "The variable ${t_blue}$key${t_reset} is ${t_red}REQUIRED${t_reset}."
    echo -e "$help"
    local val
    while true; do
      read -r -s -p "> Enter $key: " val || true
      echo
      val="$(trim_val "$val")"
      if [[ -n "${val}" ]]; then
        set_env_var "$key" "$val"
        ok "$key saved to .env"
        break
      else
        warn "$key cannot be empty."
      fi
    done
  else
    info "$key is already set; keeping existing value."
  fi
}

confirm() {
  local prompt="${1:-Are you sure?} [y/N] "
  read -r -p "$prompt" ans || true
  [[ "${ans:-}" == "y" || "${ans:-}" == "Y" ]]
}

is_macos() { [[ "$(uname -s)" == "Darwin" ]]; }
is_linux() { [[ "$(uname -s)" == "Linux" ]]; }

#############################################
# Conda helpers (respect: 注意没有conda不要丢出来)
#############################################
have_conda() { command -v conda >/dev/null 2>&1; }

conda_shell_hook() {
  if have_conda; then
    eval "$(conda shell.bash hook)"
    return 0
  fi
  if [[ -x "$DEFAULT_MINICONDA_PREFIX/bin/conda" ]]; then
    eval "$("$DEFAULT_MINICONDA_PREFIX/bin/conda" shell.bash hook)"
    return 0
  fi
  return 1
}

install_miniconda() {
  local os arch fname url
  os="$(uname -s)"
  arch="$(uname -m)"
  if is_macos; then
    case "$arch" in
      arm64)   fname="Miniconda3-latest-MacOSX-arm64.sh" ;;
      x86_64)  fname="Miniconda3-latest-MacOSX-x86_64.sh" ;;
      *) die "Unsupported macOS architecture: $arch" ;;
    esac
  elif is_linux; then
    case "$arch" in
      x86_64)  fname="Miniconda3-latest-Linux-x86_64.sh" ;;
      aarch64|arm64) fname="Miniconda3-latest-Linux-aarch64.sh" ;;
      *) die "Unsupported Linux architecture: $arch" ;;
    esac
  else
    die "Unsupported OS. Windows users: see windows_proj_env_setup.md."
  fi
  url="https://repo.anaconda.com/miniconda/$fname"
  info "Downloading Miniconda: $url"
  local dl="/tmp/$fname"
  curl -fsSL "$url" -o "$dl" || die "Failed to download Miniconda"
  bash "$dl" -b -p "$DEFAULT_MINICONDA_PREFIX" || die "Miniconda install failed"
  rm -f "$dl"
  eval "$("$DEFAULT_MINICONDA_PREFIX/bin/conda" shell.bash hook)"
  ok "Miniconda installed at $DEFAULT_MINICONDA_PREFIX"
  conda config --set auto_activate_base false || true
  conda update -y -n base -c defaults conda || true
}

ensure_conda() {
  if conda_shell_hook; then
    ok "Conda is available."
    return 0
  fi
  echo
  warn "Conda was not found."
  echo "注意：没有 conda 不要丢出来。是否下载 Miniconda？"
  if confirm "Install Miniconda to $DEFAULT_MINICONDA_PREFIX now?"; then
    install_miniconda
  else
    die "Conda is required for this setup. Please install Miniconda/Anaconda and re-run."
  fi
}

ensure_conda_env() {
  ensure_conda
  if conda env list | awk '{print $1}' | grep -qx "$CONDA_ENV"; then
    info "Conda env '$CONDA_ENV' already exists."
    local ver
    ver="$(conda run -n "$CONDA_ENV" python -c 'import sys;print(".".join(map(str,sys.version_info[:3])))' 2>/dev/null || true)"
    if [[ "${ver:-}" != "$PY_VERSION" ]]; then
      warn "Env '$CONDA_ENV' Python is $ver, expected $PY_VERSION. Proceeding anyway."
    fi
  else
    info "Creating conda env '$CONDA_ENV' with Python $PY_VERSION ..."
    conda create -y -n "$CONDA_ENV" "python=$PY_VERSION"
  fi
  # shellcheck disable=SC1090
  conda activate "$CONDA_ENV"
  ok "Activated env '$CONDA_ENV'. Python: $(python --version 2>&1)"
}

#############################################
# .env management (never clear existing content)
#############################################
create_env_if_missing() {
  if [[ -f "$ENV_FILE" ]]; then
    info "Found existing .env at repo root (will NOT overwrite)."
    return 0
  fi
  info "No .env found. Creating with Supabase defaults; will prompt for required APIs."
  cat > "$ENV_FILE" <<EOF
# ========= Oliver Root Environment =========

# Core Supabase configuration (project defaults)
SUPABASE_URL=$DEFAULT_SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY=$DEFAULT_SUPABASE_SERVICE_ROLE_KEY

# 兼容变量（部分代码用 SUPABASE_KEY）
SUPABASE_KEY=\${SUPABASE_SERVICE_ROLE_KEY}

# --- Google Cloud Configuration (LEGACY) ---
GOOGLE_CLOUD_PROJECT=<your-key>
GOOGLE_APPLICATION_CREDENTIALS=<your-key,a .json doc>

# --- Google Gemini API Configuration (get from aistudio.google.com/apikey for free) ---
# REQUIRED: Left empty on purpose; setup.sh will prompt you.
GEMINI_API_KEY=

# --- OpenAI/Anthropic API Configuration (optional, paid service) ---
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>

# --- Cerebras AI API Configuration (get from https://cloud.cerebras.ai/?redirect=/platform/apikeys for free) ---
# REQUIRED: Left empty on purpose; setup.sh will prompt you.
CEREBRAS_API_KEY=
EOF
  chmod 600 "$ENV_FILE" || true
  ok "Created $ENV_FILE"
}

check_supabase_and_warn() {
  local url key
  url="$(get_env_var SUPABASE_URL || true)"
  key="$(get_env_var SUPABASE_SERVICE_ROLE_KEY || true)"
  if [[ -z "${url:-}" || -z "${key:-}" ]]; then
    warn "SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY missing. Setting project defaults."
    [[ -z "${url:-}" ]] && set_env_var SUPABASE_URL "$DEFAULT_SUPABASE_URL"
    [[ -z "${key:-}" ]] && set_env_var SUPABASE_SERVICE_ROLE_KEY "$DEFAULT_SUPABASE_SERVICE_ROLE_KEY"
  else
    if [[ "$url" != "$DEFAULT_SUPABASE_URL" || "$key" != "$DEFAULT_SUPABASE_SERVICE_ROLE_KEY" ]]; then
      warn "Your existing SUPABASE_* differs from project defaults."
      info "Proceeding with your current values. If this is unintentional, edit $ENV_FILE."
    else
      ok "Supabase values match project defaults."
    fi
  fi
  # Ensure compatibility var exists but do NOT overwrite if already present
  local compat
  compat="$(get_env_var SUPABASE_KEY || true)"
  if [[ -z "${compat:-}" ]]; then
    set_env_var SUPABASE_KEY '${SUPABASE_SERVICE_ROLE_KEY}'
    ok "Added SUPABASE_KEY compatibility variable."
  fi
}

collect_required_keys() {
  prompt_secret_required "GEMINI_API_KEY" "$(cat <<'MSG'
Get a free Gemini API key here:
  - https://aistudio.google.com/apikey
Paste it here; input will be hidden.
MSG
)"
  prompt_secret_required "CEREBRAS_API_KEY" "$(cat <<'MSG'
Create a free Cerebras API key here:
  - https://cloud.cerebras.ai/?redirect=/platform/apikeys
Paste it here; input will be hidden.
MSG
)"
  # Final validation: both must be present (and not placeholders)
  local g c
  g="$(get_env_var GEMINI_API_KEY || true)"
  c="$(get_env_var CEREBRAS_API_KEY || true)"
  if is_empty_or_placeholder "${g:-}"; then die "GEMINI_API_KEY is required."; fi
  if is_empty_or_placeholder "${c:-}"; then die "CEREBRAS_API_KEY is required."; fi
  chmod 600 "$ENV_FILE" || true
}

copy_service_envs_if_present() {
  if [[ -d "$BACKEND_DIR" && -f "$BACKEND_DIR/.env.example" && ! -f "$BACKEND_DIR/.env" ]]; then
    cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
    ok "Copied backend/.env.example -> backend/.env"
  fi
  if [[ -d "$RAG_DIR" && -f "$RAG_DIR/.env.example" && ! -f "$RAG_DIR/.env" ]]; then
    cp "$RAG_DIR/.env.example" "$RAG_DIR/.env"
    ok "Copied machine_learning/rag_system/.env.example -> machine_learning/rag_system/.env"
  fi
}

export_root_env() {
  # Export only keys we care about, skipping empty or <...> placeholders.
  # Do NOT source the entire .env, because placeholders like <your-key>
  # are parsed as shell redirections by bash when sourced.

  local keys=(
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY
    SUPABASE_KEY
    GOOGLE_CLOUD_PROJECT
    GOOGLE_APPLICATION_CREDENTIALS
    GEMINI_API_KEY
    OPENAI_API_KEY
    ANTHROPIC_API_KEY
    CEREBRAS_API_KEY
  )

  local k v
  for k in "${keys[@]}"; do
    v="$(get_env_var "$k" || true)"
    # export only if present and not a placeholder/empty
    if ! is_empty_or_placeholder "${v:-}"; then
      export "$k=$v"
    fi
  done
}
#############################################
# Dependency installation
#############################################
install_python_requirements() {
  info "Installing Python dependencies into conda env '$CONDA_ENV'..."
  pushd "$ROOT_DIR" >/dev/null

  if [[ -f "$BACKEND_DIR/requirements.txt" ]]; then
    python -m pip install -r "$BACKEND_DIR/requirements.txt"
  else
    warn "Missing $BACKEND_DIR/requirements.txt (skipping)"
  fi

  if [[ -f "$PDF_PROC_DIR/requirements.txt" ]]; then
    python -m pip install -r "$PDF_PROC_DIR/requirements.txt"
  else
    warn "Missing $PDF_PROC_DIR/requirements.txt (skipping)"
  fi

  local pip_args=()
  if [[ -f "$ROOT_DIR/constraints.txt" ]]; then
    pip_args+=(-c "$ROOT_DIR/constraints.txt" --upgrade --upgrade-strategy eager)
  fi
  if [[ -f "$RAG_DIR/requirements.txt" ]]; then
    python -m pip install -r "$RAG_DIR/requirements.txt" "${pip_args[@]}"
  else
    warn "Missing $RAG_DIR/requirements.txt (skipping)"
  fi

  if [[ -f "$AGENT_DIR/requirements.txt" ]]; then
    python -m pip install -r "$AGENT_DIR/requirements.txt"
  else
    warn "Missing $AGENT_DIR/requirements.txt (skipping)"
  fi

  popd >/dev/null
  ok "Python dependencies installed."
}

install_frontend_deps() {
  if [[ ! -d "$FRONTEND_DIR" ]]; then
    warn "Frontend directory not found; skipping npm install."
    return 0
  fi
  if ! command -v npm >/dev/null 2>&1; then
    warn "npm not found. Frontend will not be started. Install Node.js (>=18) and re-run start."
    return 0
  fi
  pushd "$FRONTEND_DIR" >/dev/null
  info "Installing frontend dependencies (npm ci)..."
  npm ci
  popd >/dev/null
  ok "Frontend dependencies installed."
}

#############################################
# Process control (start/stop/status)
#############################################
is_running() {
  local pid_file="$1"
  [[ -f "$pid_file" ]] || return 1
  local pid
  pid="$(cat "$pid_file" 2>/dev/null || true)"
  [[ -n "${pid:-}" && -d "/proc/$pid" ]] && return 0
  if ps -p "${pid:-0}" >/dev/null 2>&1; then return 0; fi
  return 1
}

start_backend() {
  [[ -d "$BACKEND_DIR" ]] || { warn "No backend directory; skipping backend start."; return; }
  export_root_env
  local log="$LOG_DIR/backend.log" pidf="$PID_DIR/backend.pid"
  info "Starting Backend (port $BACKEND_PORT) ..."
  ( cd "$ROOT_DIR" && PYTHONPATH="$BACKEND_DIR" nohup python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port "$BACKEND_PORT" >>"$log" 2>&1 & echo $! >"$pidf" )
  ok "Backend started. Log: $log"
}

start_pdf() {
  [[ -d "$PDF_PROC_DIR" ]] || { warn "No pdf_processor directory; skipping PDF service."; return; }
  export_root_env
  local log="$LOG_DIR/pdf_processor.log" pidf="$PID_DIR/pdf_processor.pid"
  info "Starting PDF Processor (port $PDF_PORT) ..."
  ( cd "$ROOT_DIR" && PYTHONPATH="$ML_DIR" nohup python -m uvicorn pdf_processor.main:app --reload --host 0.0.0.0 --port "$PDF_PORT" >>"$log" 2>&1 & echo $! >"$pidf" )
  ok "PDF Processor started. Log: $log"
}

start_rag() {
  [[ -d "$RAG_DIR" ]] || { warn "No rag_system directory; skipping RAG service."; return; }
  export_root_env
  local log="$LOG_DIR/rag_system.log" pidf="$PID_DIR/rag_system.pid"
  info "Starting RAG System (port $RAG_PORT) ..."
  ( cd "$ROOT_DIR" && PYTHONPATH="$ML_DIR" nohup python -m uvicorn rag_system.app.main:app --reload --host 0.0.0.0 --port "$RAG_PORT" >>"$log" 2>&1 & echo $! >"$pidf" )
  ok "RAG System started. Log: $log"
}

start_agent() {
  [[ -d "$AGENT_DIR" ]] || { warn "No ai_agents directory; skipping Agent service."; return; }
  export_root_env
  local log="$LOG_DIR/ai_agents.log" pidf="$PID_DIR/ai_agents.pid"
  info "Starting Agent System (port $AGENT_PORT) ..."
  ( cd "$ROOT_DIR" && PYTHONPATH="$ML_DIR" nohup python -m uvicorn ai_agents.app.main:app --reload --host 0.0.0.0 --port "$AGENT_PORT" >>"$log" 2>&1 & echo $! >"$pidf" )
  ok "Agent System started. Log: $log"
}

start_frontend() {
  [[ -d "$FRONTEND_DIR" ]] || { warn "No frontend directory; skipping frontend."; return; }
  if ! command -v npm >/dev/null 2>&1; then
    warn "npm not found; skipping frontend. Install Node.js and rerun ./setup.sh start"
    return
  fi
  local log="$LOG_DIR/frontend.log" pidf="$PID_DIR/frontend.pid"
  info "Starting Frontend (npm run dev) ..."
  ( cd "$FRONTEND_DIR" && nohup npm run dev >>"$log" 2>&1 & echo $! >"$pidf" )
  ok "Frontend started. Log: $log"
}

stop_service() {
  local name="$1" pidf="$PID_DIR/$1.pid"
  if is_running "$pidf"; then
    local pid; pid="$(cat "$pidf" 2>/dev/null || true)"
    info "Stopping $name (PID $pid)..."
    kill "$pid" 2>/dev/null || true
    sleep 1
    if ps -p "$pid" >/dev/null 2>&1; then
      warn "$name did not stop gracefully; sending SIGKILL."
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$pidf"
    ok "$name stopped."
  else
    info "$name is not running."
    rm -f "$pidf" || true
  fi
}

status_service() {
  local name="$1" pidf="$PID_DIR/$1.pid"
  if is_running "$pidf"; then
    echo -e "  ${t_green}●${t_reset} $name (pid $(cat "$pidf"))"
  else
    echo -e "  ${t_red}○${t_reset} $name"
  fi
}

start_all() {
  ensure_dirs
  start_backend
  start_pdf
  start_rag
  start_agent
  install_frontend_deps
  start_frontend
  ok "All available services started."
  echo
  echo "Endpoints:"
  echo "  Backend:       http://localhost:$BACKEND_PORT"
  echo "  PDF Processor: http://localhost:$PDF_PORT"
  echo "  RAG System:    http://localhost:$RAG_PORT"
  echo "  Agent System:  http://localhost:$AGENT_PORT"
  echo "  Frontend:      (see frontend log for URL, typically http://localhost:5173)"
  echo
  echo "Logs: $LOG_DIR"
}

stop_all() {
  stop_service "frontend"
  stop_service "ai_agents"
  stop_service "rag_system"
  stop_service "pdf_processor"
  stop_service "backend"
}

status_all() {
  echo "Service status:"
  status_service "backend"
  status_service "pdf_processor"
  status_service "rag_system"
  status_service "ai_agents"
  status_service "frontend"
}

#############################################
# Main flows
#############################################
do_setup_only() {
  echo
  info "=== Oliver Setup ==="
  if [[ "$(uname -s)" == "MINGW"* || "$(uname -s)" == "MSYS"* || "$(uname -s)" == "CYGWIN"* ]]; then
    die "Windows detected. Please follow windows_proj_env_setup.md."
  fi

  create_env_if_missing
  check_supabase_and_warn
  collect_required_keys

  ensure_conda_env
  install_python_requirements
  copy_service_envs_if_present

  ok "Setup complete."
}

do_setup_and_run() {
  do_setup_only
  start_all
}

usage() {
  cat <<USAGE
Usage: $(basename "$0") [command]

Commands:
  (no args)   Setup + start all services (default)
  setup       Setup only (no services started)
  start       Start all services (assumes setup done)
  stop        Stop all services started by this script
  status      Show status of services
USAGE
}

#############################################
# Entrypoint
#############################################
cmd="${1:-}"
case "$cmd" in
  "")       do_setup_and_run ;;
  setup)    do_setup_only ;;
  start)    start_all ;;
  stop)     stop_all ;;
  status)   status_all ;;
  -h|--help|help) usage ;;
  *)        usage; exit 1 ;;
esac
