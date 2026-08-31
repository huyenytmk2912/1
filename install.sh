#!/usr/bin/env bash
set -euo pipefail

# One-command Khương local agent bootstrap for Linux VPS.
# Installs Ollama, Qwen-Agent, MCP tooling, a resource-aware local model,
# and a chat launcher. No API keys are written.

APP_DIR="${KHUONG_HOME:-$HOME/khuong-local}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log(){ printf '\n[KHUONG] %s\n' "$*"; }
need_cmd(){ command -v "$1" >/dev/null 2>&1; }

if [ "$(id -u)" -eq 0 ]; then SUDO=""; else SUDO="sudo"; fi

log "Checking host"
$PYTHON_BIN - <<'PY'
import os, shutil
print("Python:", shutil.which("python3") or shutil.which("python"))
print("CPU cores:", os.cpu_count())
try:
    ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024**3
    print("RAM GiB:", round(ram, 1))
except Exception:
    print("RAM GiB: unknown")
PY

RAM_GIB="$($PYTHON_BIN - <<'PY'
import os
try:
    print(int(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024**3))
except Exception:
    print(0)
PY
)"

if ! need_cmd "$PYTHON_BIN"; then
  echo "Python 3 is required."; exit 1
fi

if ! need_cmd git; then
  log "Installing git"
  if command -v apt-get >/dev/null 2>&1; then $SUDO apt-get update && $SUDO apt-get install -y git curl
  elif command -v dnf >/dev/null 2>&1; then $SUDO dnf install -y git curl
  else echo "Please install git and curl, then rerun."; exit 1; fi
fi

if ! need_cmd curl; then
  if command -v apt-get >/dev/null 2>&1; then $SUDO apt-get update && $SUDO apt-get install -y curl
  elif command -v dnf >/dev/null 2>&1; then $SUDO dnf install -y curl
  else echo "curl is required."; exit 1; fi
fi

log "Installing Ollama if missing"
if ! need_cmd ollama; then
  curl -fsSL https://ollama.com/install.sh | $SUDO sh
fi

if ! pgrep -x ollama >/dev/null 2>&1; then
  nohup ollama serve >"$HOME/ollama.log" 2>&1 &
  sleep 3
fi

log "Installing Python agent stack"
mkdir -p "$APP_DIR"
$PYTHON_BIN -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
python -m pip install --upgrade pip
python -m pip install -U 'qwen-agent[mcp]'

# Resource-aware default. Users can override KHUONG_MODEL before rerunning.
if [ "$RAM_GIB" -ge 32 ]; then
  DEFAULT_MODEL="qwen3:8b"
elif [ "$RAM_GIB" -ge 16 ]; then
  DEFAULT_MODEL="qwen3:4b"
elif [ "$RAM_GIB" -ge 8 ]; then
  DEFAULT_MODEL="qwen3.5:2b"
elif [ "$RAM_GIB" -ge 4 ]; then
  DEFAULT_MODEL="qwen3.5:0.8b"
else
  echo "Less than 4 GiB RAM detected; refusing automatic model download."; exit 1
fi

MODEL="${KHUONG_MODEL:-$DEFAULT_MODEL}"
log "Pulling local model: $MODEL"
ollama pull "$MODEL"

# Optional larger model, never pulled automatically.
cat > "$APP_DIR/models.txt" <<'EOF'
# Optional models (choose only if the VPS can handle them):
# qwen3.5:0.8b
# qwen3.5:2b
# qwen3:4b
# qwen3:8b
# Qwen3-Coder-30B-A3B-Instruct (large; use a compatible quantized deployment)
EOF

cat > "$APP_DIR/config.env" <<EOF
KHUONG_MODEL_SERVER=http://127.0.0.1:11434/v1
KHUONG_MODEL=$MODEL
KHUONG_API_KEY=EMPTY
KHUONG_APP_DIR=$APP_DIR
EOF

cat > "$APP_DIR/mcp.json" <<EOF
{
  "mcpServers": {
    "time": {"command": "uvx", "args": ["mcp-server-time", "--local-timezone=Asia/Tokyo"]},
    "fetch": {"command": "uvx", "args": ["mcp-server-fetch"]}
  }
}
EOF

cat > "$APP_DIR/chat.py" <<'PY'
import json
import os
from qwen_agent.agents import Assistant

server = os.getenv('KHUONG_MODEL_SERVER', 'http://127.0.0.1:11434/v1')
model = os.getenv('KHUONG_MODEL', 'qwen3.5:2b')

llm_cfg = {
    'model': model,
    'model_server': server,
    'api_key': os.getenv('KHUONG_API_KEY', 'EMPTY'),
}

# MCP tools are optional. If uvx/tool servers are unavailable, chat still works.
tools = []
mcp_path = os.path.join(os.getenv('KHUONG_APP_DIR', os.path.expanduser('~/khuong-local')), 'mcp.json')
try:
    with open(mcp_path, encoding='utf-8') as f:
        tools = [{"mcpServers": json.load(f)["mcpServers"]}]
except Exception:
    pass

bot = Assistant(
    llm=llm_cfg,
    function_list=tools,
    system_message='Bạn là Khương, trợ lý AI local. Trả lời bằng tiếng Việt khi người dùng nói tiếng Việt. Dùng tool khi cần và kiểm tra kết quả trước khi kết luận.'
)

messages=[]
print(f'Khương local agent — {model}. Gõ /exit để thoát.')
while True:
    q=input('Bạn> ').strip()
    if q == '/exit': break
    if not q: continue
    messages.append({'role':'user','content':q})
    response=[]
    for chunk in bot.run(messages=messages):
        response=chunk
        print(chunk, end='', flush=True)
    print()
    messages.extend(response)
PY

cat > "$APP_DIR/start-chat.sh" <<EOF
#!/usr/bin/env bash
set -euo pipefail
source "$APP_DIR/.venv/bin/activate"
set -a
source "$APP_DIR/config.env"
set +a
exec python "$APP_DIR/chat.py"
EOF
chmod +x "$APP_DIR/start-chat.sh"

cat > "$APP_DIR/README.txt" <<'EOF'
Khương local agent bootstrap

Installed automatically:
- Ollama local inference runtime
- Qwen-Agent with function calling/MCP support
- Resource-aware Qwen local model
- MCP time/fetch tool configuration
- Local chat launcher

Small-to-large model options:
- qwen3.5:0.8b
- qwen3.5:2b
- qwen3:4b
- qwen3:8b
- Qwen3-Coder-30B-A3B-Instruct: optional, large/quantized deployment only

The installer intentionally does not pull a 30B model automatically. It chooses a smaller model from detected RAM.
EOF

log "Installation complete"
echo "Model: $MODEL"
echo "Agent directory: $APP_DIR"
echo "Chat: $APP_DIR/start-chat.sh"
echo "Optional model list: $APP_DIR/models.txt"
