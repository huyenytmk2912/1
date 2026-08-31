#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY=python3
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[1] %s\n' "$*"; }

log "Preparing Linux VPS"
if need apt-get; then $SUDO apt-get update; $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils
elif need dnf; then $SUDO dnf install -y python3 python3-pip curl git ca-certificates poppler-utils || $SUDO dnf install -y python3 python3-pip curl git ca-certificates
else echo "Supported Linux package manager not found (apt/dnf)."; exit 1; fi

mkdir -p "$APP_DIR"/{pipeline,collector,importers,extractors,generators,verifiers,training,evaluation,cli,data/raw,data/dataset,data/review,data/logs,data/state,config}
cp -r pipeline "$APP_DIR/" 2>/dev/null || true

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

# Copy the repository's pipeline when the script is run from a clone; otherwise fetch it.
if [ -f "$(pwd)/pipeline/dataset.py" ] && [ "$(pwd)" != "$APP_DIR" ]; then cp -f pipeline/*.py "$APP_DIR/pipeline/"; fi

cat > "$APP_DIR/run.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
cd "$APP_DIR"
export PROJECT_HOME="$APP_DIR"
export PYTHONPATH="$APP_DIR"
[ -f "$APP_DIR/config/runtime.env" ] && set -a && source "$APP_DIR/config/runtime.env" && set +a
exec python3 "$APP_DIR/cli.py" "\$@"
EOF
chmod +x "$APP_DIR/run.sh"

cat > "$APP_DIR/data/state/README.txt" <<'EOF'
Runtime state lives here. Do not commit collected data, credentials, model weights, or private source material to Git.
EOF

log "Installation complete"
echo "Project: $APP_DIR"
echo "Commands: $APP_DIR/run.sh status | build | train | evaluate"
echo "Local model: ${MODEL:-none (deterministic mode)}"
echo "Training is NEVER started automatically. Review the readiness report first."
