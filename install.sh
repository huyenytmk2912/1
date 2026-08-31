#!/usr/bin/env bash
set -Eeuo pipefail
REPO_URL="${REPO_URL:-https://github.com/huyenytmk2912/1.git}"
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY="python3"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
need(){ command -v "$1" >/dev/null 2>&1; }
log(){ printf '\n[1] %s\n' "$*"; }

log "Preparing Linux VPS"
if need apt-get; then
  $SUDO apt-get update
  $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils
elif need dnf; then
  $SUDO dnf install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils || $SUDO dnf install -y python3 python3-pip curl git ca-certificates
else
  echo "Supported Linux package manager not found (apt/dnf)."; exit 1
fi

log "Installing/updating repository"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" fetch --depth 1 origin main
  git -C "$APP_DIR" reset --hard origin/main
elif [ ! -f "$APP_DIR/cli.py" ]; then
  TMP="$(mktemp -d)"
  git clone --depth 1 "$REPO_URL" "$TMP/repo"
  mkdir -p "$APP_DIR"
  cp -a "$TMP/repo/." "$APP_DIR/"
  rm -rf "$TMP"
else
  echo "Existing non-git project found at $APP_DIR; remove it and rerun for a clean install."; exit 1
fi

mkdir -p "$APP_DIR"/{data/raw,data/inbox,data/dataset,data/review,data/logs,data/state,data/export,config}

log "Creating Python environment"
$PY -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$APP_DIR/requirements.txt" pypdf beautifulsoup4

# Model: Gemma 3 4B. Vietnamese prompts are used by the project runtime.
MODEL="gemma3:4b"

# IMPORTANT: Ollama 0.30.x changed the Linux model backend to llama.cpp/llama-server.
# Some 0.30.x package builds have shipped without llama-server, producing the exact
# HTTP 500 seen on this VPS. Pin a known stable pre-0.30 release for this project.
OLLAMA_VERSION="${OLLAMA_VERSION:-0.24.0}"

log "Installing and validating Ollama $OLLAMA_VERSION + $MODEL"
# Remove stale libraries first; the official Linux docs explicitly recommend this when reinstalling.
if need systemctl; then
  $SUDO systemctl stop ollama 2>/dev/null || true
  $SUDO systemctl disable ollama 2>/dev/null || true
fi
pkill -x ollama 2>/dev/null || true
$SUDO rm -rf /usr/lib/ollama /usr/local/lib/ollama /lib/ollama

# Use the official installer with a pinned version, not the moving latest release.
curl -fsSL https://ollama.com/install.sh | $SUDO env OLLAMA_VERSION="$OLLAMA_VERSION" sh
command -v ollama >/dev/null 2>&1 || { echo "ERROR: Ollama CLI was not installed."; exit 1; }
INSTALLED_OLLAMA="$(ollama -v | awk '{print $NF}')"
[ "$INSTALLED_OLLAMA" = "$OLLAMA_VERSION" ] || {
  echo "ERROR: requested Ollama $OLLAMA_VERSION but installed $INSTALLED_OLLAMA"; exit 1;
}
echo "Ollama version check: OK ($INSTALLED_OLLAMA)"

if need systemctl && systemctl list-unit-files ollama.service >/dev/null 2>&1; then
  $SUDO systemctl daemon-reload
  $SUDO systemctl enable --now ollama
else
  pkill -x ollama 2>/dev/null || true
  nohup ollama serve >"$APP_DIR/data/logs/ollama.log" 2>&1 &
fi

log "Checking Ollama HTTP runtime"
for i in $(seq 1 30); do
  if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then break; fi
  [ "$i" -eq 30 ] && { echo "ERROR: Ollama HTTP runtime did not become ready."; tail -n 80 "$APP_DIR/data/logs/ollama.log" 2>/dev/null || true; exit 1; }
  sleep 1
done

log "Pulling exact model: $MODEL"
ollama pull "$MODEL"

log "Validating exact model and Vietnamese inference"
TAGS="$APP_DIR/data/state/ollama-tags.json"
curl -fsS http://127.0.0.1:11434/api/tags > "$TAGS"
"$APP_DIR/.venv/bin/python" - "$TAGS" "$MODEL" <<'PY'
import json,sys
p,model=sys.argv[1:]
data=json.load(open(p,encoding='utf-8'))
names={x.get('name') for x in data.get('models',[])}
if model not in names:
    raise SystemExit(f"ERROR: exact model {model} is not present in Ollama tags: {sorted(names)}")
print(f"model check: OK ({model})")
PY

PAYLOAD="$APP_DIR/data/state/model-smoke.json"
cat > "$PAYLOAD" <<EOF
{"model":"$MODEL","prompt":"Trả lời bằng tiếng Việt. Hãy trả lời đúng một từ: OK","stream":false,"options":{"temperature":0}}
EOF
RESP="$APP_DIR/data/state/model-smoke-response.json"
curl -fsS --max-time 180 http://127.0.0.1:11434/api/generate -H 'Content-Type: application/json' --data-binary @"$PAYLOAD" > "$RESP"
"$APP_DIR/.venv/bin/python" - "$RESP" "$MODEL" <<'PY'
import json,sys
p,model=sys.argv[1:]
r=json.load(open(p,encoding='utf-8'))
if r.get('model') != model:
    raise SystemExit(f"ERROR: inference used {r.get('model')!r}, expected {model!r}")
text=(r.get('response') or '').strip()
if not text or 'ok' not in text.lower():
    raise SystemExit(f"ERROR: Vietnamese model smoke test failed; response={text!r}")
print(f"inference check: OK ({model}; Vietnamese prompt accepted)")
PY

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
LANGUAGE=vi
OLLAMA_VERSION=$OLLAMA_VERSION
EOF

cat > "$APP_DIR/run.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"
export PROJECT_HOME="$APP_DIR"
export PYTHONPATH="$APP_DIR"
set -a; source "$APP_DIR/config/runtime.env"; set +a
case "${1:-status}" in
  status|build|readiness|export|verify|check-leakage|version|pipeline) exec "$APP_DIR/.venv/bin/python" "$APP_DIR/cli.py" "$1" ;;
  worker) exec "$APP_DIR/.venv/bin/python" "$APP_DIR/worker.py" ;;
  *) echo "Usage: $APP_DIR/run.sh {status|build|worker|readiness|export|verify|check-leakage|version|pipeline}"; exit 2 ;;
esac
EOF
chmod +x "$APP_DIR/run.sh"

log "Running installation self-check"
[ -x "$APP_DIR/run.sh" ] && [ -f "$APP_DIR/cli.py" ] && [ -f "$APP_DIR/worker.py" ] && [ -d "$APP_DIR/.venv" ]
"$APP_DIR/.venv/bin/python" -c 'import pypdf,bs4; print("document parsers: OK")'
"$APP_DIR/run.sh" status

log "Installation complete"
echo "Project: $APP_DIR"
echo "Local AI: $MODEL"
echo "Language: Vietnamese (vi)"
echo "Ollama: $OLLAMA_VERSION"
echo "Model smoke test: PASS"
echo "Start worker: $APP_DIR/run.sh worker"
echo "Training is disabled on VPS 1."
