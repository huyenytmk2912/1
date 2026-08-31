#!/usr/bin/env bash
set -euo pipefail
REPO_URL="${REPO_URL:-https://github.com/huyenytmk2912/1.git}"
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY=python3
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[1] %s\n' "$*"; }

log "Preparing Linux VPS"
if need apt-get; then $SUDO apt-get update; $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils
elif need dnf; then $SUDO dnf install -y python3 python3-pip curl git ca-certificates poppler-utils || $SUDO dnf install -y python3 python3-pip curl git ca-certificates
else echo "Supported Linux package manager not found (apt/dnf)."; exit 1; fi

# A fresh VPS needs the complete repository, not just the installer.
if [ ! -f "$APP_DIR/cli.py" ]; then
  TMP="$(mktemp -d)"
  git clone --depth 1 "$REPO_URL" "$TMP/repo"
  mkdir -p "$APP_DIR"
  cp -a "$TMP/repo/." "$APP_DIR/"
  rm -rf "$TMP"
fi
mkdir -p "$APP_DIR"/{data/raw,data/dataset,data/review,data/logs,data/state,config}

RAM="$($PY - <<'PY'
import os
try: print(int(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3))
except: print(0)
PY
)"
MODEL="${MODEL:-}"
if [ -z "$MODEL" ] && [ "$RAM" -ge 8 ]; then MODEL="qwen3.5:2b"; fi

if [ -n "$MODEL" ]; then
  log "Installing optional local AI: $MODEL"
  if ! need ollama; then curl -fsSL https://ollama.com/install.sh | $SUDO sh; fi
  if ! pgrep -x ollama >/dev/null 2>&1; then nohup ollama serve >"$APP_DIR/data/logs/ollama.log" 2>&1 & sleep 4; fi
  ollama pull "$MODEL"
fi

cat > "$APP_DIR/config/runtime.env" <<EOF
PROJECT_HOME=$APP_DIR
MODEL=$MODEL
OLLAMA_URL=http://127.0.0.1:11434
INTERVAL=1800
MAX_SOURCE_CHARS=30000
MIN_QUALITY_SCORE=0.80
AUTO_TRAIN=0
EOF

cat > "$APP_DIR/run.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$APP_DIR"
export PROJECT_HOME="$APP_DIR"
export PYTHONPATH="$APP_DIR"
set -a; source "$APP_DIR/config/runtime.env"; set +a
case "\${1:-status}" in
  status|build|train|evaluate) exec python3 "$APP_DIR/cli.py" "\$1" ;;
  worker) exec python3 "$APP_DIR/worker.py" ;;
  *) echo "Usage: $APP_DIR/run.sh {status|build|worker|train|evaluate}"; exit 2;;
esac
EOF
chmod +x "$APP_DIR/run.sh"

log "Installation complete"
echo "Project: $APP_DIR"
echo "Run once: $APP_DIR/run.sh build"
echo "Worker:   $APP_DIR/run.sh worker"
echo "Training: $APP_DIR/run.sh train"
echo "Local AI: ${MODEL:-none (deterministic mode)}"
echo "Training is never started automatically."
