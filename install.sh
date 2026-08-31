#!/usr/bin/env bash
set -euo pipefail

# Khương VPS bootstrap: lightweight hybrid dataset agent.
# Local inference is optional at architecture level, but the default is a tiny
# Qwen model through Ollama so the VPS can operate without an external API.

APP_DIR="${KHUONG_HOME:-$HOME/khuong}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
SUDO=""
[ "$(id -u)" -ne 0 ] && SUDO="sudo"

need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[KHUONG] %s\n' "$*"; }

if ! need "$PYTHON_BIN"; then echo "Python 3 is required."; exit 1; fi
if ! need curl || ! need git; then
  if need apt-get; then $SUDO apt-get update && $SUDO apt-get install -y curl git
  elif need dnf; then $SUDO dnf install -y curl git
  else echo "Install curl and git first."; exit 1; fi
fi

mkdir -p "$APP_DIR/data/raw" "$APP_DIR/data" "$APP_DIR/agent"

RAM_GIB="$($PYTHON_BIN - <<'PY'
import os
try: print(int(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3))
except Exception: print(0)
PY
)"

# Small model by default; override KHUONG_MODEL before running.
if [ -z "${KHUONG_MODEL:-}" ]; then
  if [ "$RAM_GIB" -ge 8 ]; then KHUONG_MODEL="qwen3.5:2b"
  else KHUONG_MODEL="qwen3.5:0.8b"; fi
fi

log "Installing Ollama"
if ! need ollama; then curl -fsSL https://ollama.com/install.sh | $SUDO sh; fi
if ! pgrep -x ollama >/dev/null 2>&1; then nohup ollama serve >"$APP_DIR/ollama.log" 2>&1 & sleep 3; fi

log "Pulling $KHUONG_MODEL"
ollama pull "$KHUONG_MODEL"

cat > "$APP_DIR/agent/config.env" <<EOF
KHUONG_HOME=$APP_DIR
KHUONG_MODEL=$KHUONG_MODEL
OLLAMA_URL=http://127.0.0.1:11434
KHUONG_INTERVAL=900
EOF

cat > "$APP_DIR/agent/requirements.txt" <<'EOF'
# Runtime uses only the Python standard library.
EOF

# Keep the checked-in worker in sync with this deployment.
if [ -f "$APP_DIR/agent/agent.py" ]; then :; fi

log "Installing user service"
mkdir -p "$HOME/.config/systemd/user"
cp "$APP_DIR/agent/khuong-worker.service" "$HOME/.config/systemd/user/khuong-worker.service"
# The service expects agent.py at $APP_DIR/agent; use an absolute override generated here.
sed -i "s#%h/khuong/agent#${APP_DIR}/agent#g; s#%h/khuong#${APP_DIR}#g" "$HOME/.config/systemd/user/khuong-worker.service"

systemctl --user daemon-reload || true
systemctl --user enable --now khuong-worker.service || true

cat > "$APP_DIR/README.txt" <<EOF
Khương installed.

Home: $APP_DIR
Model: $KHUONG_MODEL
Raw input: $APP_DIR/data/raw/*.txt
Dataset: $APP_DIR/data/dataset.jsonl
Worker: systemctl --user status khuong-worker

This version intentionally does NOT perform uncontrolled web crawling.
Add source adapters only after provenance/license filtering is implemented.
EOF

log "Done"
echo "Model: $KHUONG_MODEL"
echo "Data: $APP_DIR/data"
echo "Worker: systemctl --user status khuong-worker"
