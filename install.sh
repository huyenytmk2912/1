#!/usr/bin/env bash
set -Eeuo pipefail
REPO_URL="${REPO_URL:-https://github.com/huyenytmk2912/1.git}"
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY="python3"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[1] %s\n' "$*"; }
log "Preparing Linux VPS"
if need apt-get; then $SUDO apt-get update; $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils
elif need dnf; then $SUDO dnf install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils || $SUDO dnf install -y python3 python3-pip curl git ca-certificates
else echo "Supported Linux package manager not found (apt/dnf)."; exit 1; fi
log "Installing/updating repository"
if [ -d "$APP_DIR/.git" ]; then git -C "$APP_DIR" fetch --depth 1 origin main; git -C "$APP_DIR" reset --hard origin/main
elif [ ! -f "$APP_DIR/cli.py" ]; then TMP="$(mktemp -d)"; git clone --depth 1 "$REPO_URL" "$TMP/repo"; mkdir -p "$APP_DIR"; cp -a "$TMP/repo/." "$APP_DIR/"; rm -rf "$TMP"
else echo "Existing non-git project found at $APP_DIR; keeping it. Remove it and rerun to reinstall cleanly."; exit 1; fi
mkdir -p "$APP_DIR"/{data/raw,data/inbox,data/dataset,data/review,data/logs,data/state,data/export,config}
log "Creating Python environment"
$PY -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$APP_DIR/requirements.txt" pypdf beautifulsoup4
RAM="$($PY - <<'PY'
import os
try: print(int(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3))
except: print(0)
PY
)"
MODEL="${MODEL:-}"
if [ -z "$MODEL" ] && [ "$RAM" -ge 8 ]; then MODEL="qwen3.5:2b"; fi
if [ -n "$MODEL" ]; then
  log "Preparing optional local AI: $MODEL"
  if ! need ollama; then if ! curl -fsSL https://ollama.com/install.sh | $SUDO sh; then echo "WARNING: Ollama installation failed; continuing without local AI."; MODEL=""; fi; fi
  if [ -n "$MODEL" ]; then
    if ! pgrep -x ollama >/dev/null 2>&1; then nohup ollama serve >"$APP_DIR/data/logs/ollama.log" 2>&1 & sleep 4; fi
    if ! ollama pull "$MODEL"; then echo "WARNING: model pull failed; continuing without local AI."; MODEL=""; fi
  fi
fi
log "Writing runtime launcher"
cat > "$APP_DIR/config/runtime.env" <<EOF
PROJECT_HOME=$APP_DIR
MODEL=$MODEL
VERIFIER_MODEL=$MODEL
OLLAMA_URL=http://127.0.0.1:11434
INTERVAL=1800
MAX_SOURCE_CHARS=30000
MIN_QUALITY_SCORE=0.80
AUTO_TRAIN=0
EOF
cat > "$APP_DIR/run.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"; export PROJECT_HOME="$APP_DIR"; export PYTHONPATH="$APP_DIR"
set -a; source "$APP_DIR/config/runtime.env"; set +a
case "${1:-status}" in
 status|build|readiness|export|verify|check-leakage|version|pipeline) exec "$APP_DIR/.venv/bin/python" "$APP_DIR/cli.py" "$1" ;;
 worker) exec "$APP_DIR/.venv/bin/python" "$APP_DIR/worker.py" ;;
 *) echo "Usage: $APP_DIR/run.sh {status|build|worker|readiness|export|verify|check-leakage|version|pipeline}"; exit 2;;
esac
EOF
chmod +x "$APP_DIR/run.sh"
log "Running installation self-check"
[ -x "$APP_DIR/run.sh" ] && [ -f "$APP_DIR/cli.py" ] && [ -f "$APP_DIR/worker.py" ] && [ -d "$APP_DIR/.venv" ]
"$APP_DIR/.venv/bin/python" -c 'import pypdf,bs4; print("document parsers: OK")'
"$APP_DIR/run.sh" status
log "Installation complete"
echo "Project: $APP_DIR"
echo "Local AI: ${MODEL:-none (deterministic mode)}"
echo "Start worker: $APP_DIR/run.sh worker"
echo "Training is disabled on VPS 1."
