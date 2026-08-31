#!/usr/bin/env bash
set -euo pipefail
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY=python3; SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[1] %s\n' "$*"; }
log "Installing base packages"
if need apt-get; then $SUDO apt-get update; $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils
elif need dnf; then $SUDO dnf install -y python3 python3-pip curl git ca-certificates poppler-utils || $SUDO dnf install -y python3 python3-pip curl git ca-certificates
else echo "Supported Linux package manager not found (apt/dnf)."; exit 1; fi
mkdir -p "$APP_DIR"/{agent,data/raw,data/dataset,data/logs,data/state}
RAM="$($PY - <<'PY'
import os
try: print(int(os.sysconf('SC_PAGE_SIZE')*os.sysconf('SC_PHYS_PAGES')/1024**3))
except: print(0)
PY
)"
MODEL="${MODEL:-}"; if [ -z "$MODEL" ] && [ "$RAM" -ge 8 ]; then MODEL="qwen3.5:2b"; fi
if [ -n "$MODEL" ]; then
  log "Installing optional local inference"
  if ! need ollama; then curl -fsSL https://ollama.com/install.sh | $SUDO sh; fi
  if ! pgrep -x ollama >/dev/null 2>&1; then nohup ollama serve >"$APP_DIR/data/logs/ollama.log" 2>&1 & sleep 4; fi
  ollama pull "$MODEL"
fi
cat > "$APP_DIR/agent/config.env" <<EOF
PROJECT_HOME=$APP_DIR
MODEL=$MODEL
OLLAMA_URL=http://127.0.0.1:11434
INTERVAL=1800
MAX_DOC_CHARS=30000
ONCE=0
EOF
log "Installing persistent worker"
mkdir -p "$HOME/.config/systemd/user"
cat > "$HOME/.config/systemd/user/training-data-agent.service" <<EOF
[Unit]
Description=Training Data Agent
After=network-online.target
Wants=network-online.target
[Service]
Type=simple
WorkingDirectory=$APP_DIR
EnvironmentFile=$APP_DIR/agent/config.env
ExecStart=$PY $APP_DIR/agent/agent.py
Restart=always
RestartSec=15
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload || true
systemctl --user enable --now training-data-agent.service || true
cat > "$APP_DIR/START.txt" <<EOF
Project: $APP_DIR
Worker: systemctl --user status training-data-agent
Dataset: $APP_DIR/data/dataset
Model: ${MODEL:-none; deterministic fallback enabled}

The worker discovers public arXiv material, records provenance, creates structured training examples for reasoning/coding/trading, validates them, deduplicates by source hash, and creates train/validation/test splits. It does not automatically scrape arbitrary copyrighted websites.
EOF
log "Ready"
echo "Project: $APP_DIR"; echo "Worker: systemctl --user status training-data-agent"; echo "Dataset: $APP_DIR/data/dataset"
