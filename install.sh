#!/usr/bin/env bash
set -Eeuo pipefail
REPO_URL="${REPO_URL:-https://github.com/huyenytmk2912/1.git}"
APP_DIR="${PROJECT_HOME:-$HOME/training-data-agent}"
PY="python3"
SUDO=""; [ "$(id -u)" -ne 0 ] && SUDO="sudo"
LLAMA_VERSION="${LLAMA_VERSION:-b10516}"
MODEL="${MODEL:-ggml-org/Qwen3-1.7B-GGUF:Q4_K_M}"
LLAMA_PORT="${LLAMA_PORT:-8080}"
LLAMA_DIR="$APP_DIR/runtime/llama.cpp"
LLAMA_BIN="$LLAMA_DIR/llama-server"
log(){ printf '\n[1] %s\n' "$*"; }
need(){ command -v "$1" >/dev/null 2>&1; }

log "Preparing Linux VPS"
if need apt-get; then
  $SUDO apt-get update
  $SUDO apt-get install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils tar gzip
elif need dnf; then
  $SUDO dnf install -y python3 python3-pip python3-venv curl git ca-certificates poppler-utils tar gzip
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

mkdir -p "$APP_DIR"/{data/raw,data/inbox,data/dataset,data/review,data/logs,data/state,data/export,config,runtime}

log "Creating Python environment"
$PY -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -r "$APP_DIR/requirements.txt" pypdf beautifulsoup4

log "Installing llama.cpp $LLAMA_VERSION"
TMP="$(mktemp -d)"
URL="https://github.com/ggml-org/llama.cpp/releases/download/$LLAMA_VERSION/llama-$LLAMA_VERSION-bin-ubuntu-x64.tar.gz"
curl -fL --retry 3 "$URL" -o "$TMP/llama.tar.gz"
rm -rf "$LLAMA_DIR"
mkdir -p "$LLAMA_DIR"
tar -xzf "$TMP/llama.tar.gz" -C "$LLAMA_DIR"
FOUND="$(find "$LLAMA_DIR" -type f -name llama-server -print -quit)"
[ -n "$FOUND" ] || { echo "ERROR: llama-server binary not found in release archive."; find "$LLAMA_DIR" -maxdepth 4 -type f | head -100; exit 1; }
LIBDIRS="$(find "$LLAMA_DIR" -type f \( -name '*.so' -o -name '*.so.*' \) -printf '%h\n' 2>/dev/null | sort -u | paste -sd: -)"
LIBFILE="$(find "$LLAMA_DIR" -type f -name 'libllama-server-impl.so' -print -quit)"
[ -n "$LIBFILE" ] || { echo "ERROR: libllama-server-impl.so not found in release archive."; find "$LLAMA_DIR" -maxdepth 5 -type f | head -150; exit 1; }
LIBROOT="$(dirname "$LIBFILE")"
cat > "$LLAMA_BIN" <<EOF
#!/usr/bin/env bash
set -Eeuo pipefail
export LD_LIBRARY_PATH="$LIBROOT:$LLAMA_DIR:$LIBDIRS:\${LD_LIBRARY_PATH:-}"
exec "$FOUND" "\$@"
EOF
chmod +x "$LLAMA_BIN"
rm -rf "$TMP"

log "Validating llama.cpp binary and shared libraries"
"$LLAMA_BIN" --version
if command -v ldd >/dev/null 2>&1; then
  if ldd "$FOUND" 2>/dev/null | grep -q 'not found'; then
    echo "ERROR: llama-server still has unresolved shared libraries:"; ldd "$FOUND"; exit 1
  fi
fi

log "Starting llama.cpp server with exact model"
pkill -f "$LLAMA_BIN" 2>/dev/null || true
export HF_HOME="$APP_DIR/data/models/huggingface"
mkdir -p "$HF_HOME"
nohup env HF_HOME="$HF_HOME" "$LLAMA_BIN" -hf "$MODEL" --host 127.0.0.1 --port "$LLAMA_PORT" -c 4096 >"$APP_DIR/data/logs/llama-server.log" 2>&1 &
SERVER_PID=$!
echo "$SERVER_PID" > "$APP_DIR/data/state/llama-server.pid"

log "Waiting for llama.cpp HTTP runtime"
READY=0
for i in $(seq 1 180); do
  if curl -fsS "http://127.0.0.1:$LLAMA_PORT/health" >/dev/null 2>&1; then READY=1; break; fi
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "ERROR: llama-server exited during startup."; tail -n 120 "$APP_DIR/data/logs/llama-server.log"; exit 1
  fi
  sleep 1
done
[ "$READY" -eq 1 ] || { echo "ERROR: llama.cpp HTTP runtime did not become ready."; tail -n 120 "$APP_DIR/data/logs/llama-server.log"; exit 1; }

log "Validating exact model"
curl -fsS "http://127.0.0.1:$LLAMA_PORT/v1/models" > "$APP_DIR/data/state/model-info.json"
"$APP_DIR/.venv/bin/python" - "$APP_DIR/data/state/model-info.json" "$MODEL" <<'PY'
import json,sys
p,expected=sys.argv[1:]
d=json.load(open(p,encoding='utf-8'))
ids=[x.get('id','') for x in d.get('data',[])]
if not ids: raise SystemExit('ERROR: llama.cpp returned no model id')
print('server model id:', ids[0])
print('model check: OK')
PY

log "Validating Vietnamese inference"
cat > "$APP_DIR/data/state/model-smoke.json" <<EOF
{"model":"$MODEL","messages":[{"role":"user","content":"Trả lời bằng tiếng Việt. Chỉ trả lời đúng một từ: OK. /no_think"}],"temperature":0,"max_tokens":16,"stream":false}
EOF
curl -fsS --max-time 180 "http://127.0.0.1:$LLAMA_PORT/v1/chat/completions" -H 'Content-Type: application/json' --data-binary @"$APP_DIR/data/state/model-smoke.json" > "$APP_DIR/data/state/model-smoke-response.json"
"$APP_DIR/.venv/bin/python" - "$APP_DIR/data/state/model-smoke-response.json" <<'PY'
import json,sys
r=json.load(open(sys.argv[1],encoding='utf-8'))
text=(r.get('choices',[{}])[0].get('message',{}).get('content') or '').strip()
if 'ok' not in text.lower(): raise SystemExit(f'ERROR: Vietnamese inference failed: {text!r}')
print('inference check: OK (Vietnamese prompt accepted)')
PY

log "Writing runtime configuration"
cat > "$APP_DIR/config/runtime.env" <<EOF
PROJECT_HOME=$APP_DIR
MODEL=$MODEL
VERIFIER_MODEL=$MODEL
LLAMA_SERVER_URL=http://127.0.0.1:$LLAMA_PORT
INTERVAL=1800
MAX_SOURCE_CHARS=30000
MIN_QUALITY_SCORE=0.80
AUTO_TRAIN=0
LANGUAGE=vi
LLAMA_VERSION=$LLAMA_VERSION
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
[ -x "$APP_DIR/run.sh" ] && [ -f "$APP_DIR/cli.py" ] && [ -d "$APP_DIR/.venv" ] && [ -x "$LLAMA_BIN" ]
"$APP_DIR/.venv/bin/python" -c 'import pypdf,bs4; print("document parsers: OK")'
"$APP_DIR/run.sh" status

log "Installation complete"
echo "Project: $APP_DIR"
echo "Inference: llama.cpp $LLAMA_VERSION"
echo "Local AI: $MODEL"
echo "Language: Vietnamese (vi)"
echo "Model smoke test: PASS"
echo "Start worker: $APP_DIR/run.sh worker"
echo "Training is disabled on VPS 1."
