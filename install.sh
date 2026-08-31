#!/usr/bin/env bash
set -euo pipefail

# Khương local-agent bootstrap for Linux VPS.
# Installs a lightweight local LLM runtime, Qwen-Agent, MCP tools,
# and creates a configurable model profile. It does NOT store API keys.

APP_DIR="${KHUONG_HOME:-$HOME/khuong-local}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

log(){ printf '\n[KHUONG] %s\n' "$*"; }
need_cmd(){ command -v "$1" >/dev/null 2>&1; }

log "Checking host"
$PYTHON_BIN - <<'PY'
import os, shutil
print("Python:", shutil.which("python3") or shutil.which("python"))
print("CPU cores:", os.cpu_count())
try:
    print("RAM GiB:", round(os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES') / 1024**3, 1))
except Exception:
    print("RAM GiB: unknown")
PY

mkdir -p "$APP_DIR"

if ! need_cmd git; then
  log "Installing git"
  if command -v apt-get >/dev/null 2>&1; then sudo apt-get update && sudo apt-get install -y git
  elif command -v dnf >/dev/null 2>&1; then sudo dnf install -y git
  else echo "Please install git and rerun."; exit 1; fi
fi

if ! need_cmd "$PYTHON_BIN"; then
  echo "Python 3 is required."; exit 1
fi

log "Creating Python environment"
$PYTHON_BIN -m venv "$APP_DIR/.venv"
source "$APP_DIR/.venv/bin/activate"
python -m pip install --upgrade pip

log "Installing Qwen-Agent + MCP support"
python -m pip install -U 'qwen-agent[mcp]'

cat > "$APP_DIR/requirements-agent.txt" <<'EOF'
qwen-agent[mcp]
EOF

cat > "$APP_DIR/config.env" <<'EOF'
# Local model endpoint. Set this when you deploy Ollama/vLLM/SGLang.
KHUONG_MODEL_SERVER=http://127.0.0.1:11434/v1
KHUONG_MODEL=Qwen3-4B
KHUONG_API_KEY=EMPTY
# Optional model choices for a small VPS.
KHUONG_REASONING_MODEL=Qwen3-4B
KHUONG_CODING_MODEL=Qwen3-Coder-30B-A3B-Instruct
KHUONG_GENERAL_MODEL=Qwen3.5-2B
EOF

cat > "$APP_DIR/README.txt" <<'EOF'
Khương local-agent bootstrap

Installed:
- Python virtual environment
- Qwen-Agent with MCP support
- model/router configuration scaffold

Recommended model tiers (choose according to RAM/VRAM):
- very small: Qwen3.5-0.8B / Qwen3-1.7B
- small: Qwen3.5-2B / Qwen3-4B
- stronger: Qwen3-8B / suitable 7B-14B coding model
- upper limit: Qwen3-Coder-30B-A3B-Instruct (requires substantially more memory)

Qwen-Agent provides function calling, planning, memory, MCP and example browser/code tools.
This installer deliberately does not download a large model blindly: model selection depends on the host resources.
EOF

cat > "$APP_DIR/chat.py" <<'PY'
import os
from qwen_agent.agents import Assistant

server = os.getenv('KHUONG_MODEL_SERVER', 'http://127.0.0.1:11434/v1')
model = os.getenv('KHUONG_MODEL', 'Qwen3-4B')

llm_cfg = {
    'model': model,
    'model_server': server,
    'api_key': os.getenv('KHUONG_API_KEY', 'EMPTY'),
}

bot = Assistant(
    llm=llm_cfg,
    function_list=[],
    system_message='Bạn là Khương, một trợ lý local. Trả lời bằng tiếng Việt khi người dùng nói tiếng Việt.'
)

messages=[]
print('Khương local agent. Gõ /exit để thoát.')
while True:
    q=input('Bạn> ').strip()
    if q == '/exit': break
    messages.append({'role':'user','content':q})
    out=[]
    for chunk in bot.run(messages=messages):
        out=chunk
        print(chunk, end='', flush=True)
    print()
    messages.extend(out)
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

log "Bootstrap complete"
echo "Files: $APP_DIR"
echo "Next: install a compatible local model server, then run: $APP_DIR/start-chat.sh"
echo "No API key was stored."
