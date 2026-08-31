#!/usr/bin/env python3
import json
import os
import re
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(os.getenv("KHUONG_HOME", Path.home() / "khuong"))
DATA = ROOT / "data"
RAW = DATA / "raw"
DATASET = DATA / "dataset.jsonl"
for p in (RAW, DATA):
    p.mkdir(parents=True, exist_ok=True)

MODEL = os.getenv("KHUONG_MODEL", "qwen3.5:0.8b")
OLLAMA = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
INTERVAL = int(os.getenv("KHUONG_INTERVAL", "900"))

SYSTEM = """Bạn là Khương Data Agent. Nhiệm vụ là tạo dữ liệu huấn luyện chất lượng cao cho reasoning, coding và research. Không bịa nguồn. Khi không đủ bằng chứng, nói rõ chưa đủ dữ liệu. Mỗi mẫu phải có task, reasoning_summary ngắn, answer, domain, source và quality_notes. Không đưa bí mật, thông tin cá nhân hoặc nội dung không có quyền sử dụng vào dataset."""

def ask(prompt):
    payload = json.dumps({"model": MODEL, "system": SYSTEM, "prompt": prompt, "stream": False, "options": {"temperature": 0.2}}).encode()
    req = Request(f"{OLLAMA}/api/generate", data=payload, headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=180) as r:
        return json.loads(r.read()).get("response", "")

def clean(s):
    return re.sub(r"\s+", " ", s).strip()

def make_example(text, domain, source):
    prompt = f"Từ tài liệu dưới đây, tạo đúng MỘT JSON object hợp lệ, không markdown.\nDOMAIN: {domain}\nSOURCE: {source}\nTEXT: {text[:12000]}\nSchema: {{\"task\":str,\"reasoning_summary\":str,\"answer\":str,\"domain\":str,\"source\":str,\"quality_notes\":str}}"
    raw = ask(prompt)
    raw = raw.strip().removeprefix("```json").removesuffix("```").strip()
    obj = json.loads(raw)
    required = {"task","reasoning_summary","answer","domain","source","quality_notes"}
    if set(obj) < required or not all(isinstance(obj[k], str) and obj[k].strip() for k in required):
        raise ValueError("invalid dataset object")
    return obj

def ingest_local_files():
    made = 0
    for path in sorted(RAW.glob("*.txt")):
        text = clean(path.read_text(encoding="utf-8", errors="ignore"))
        if len(text) < 200:
            continue
        domain = "coding" if any(x in text.lower() for x in ("python", "javascript", "code", "api")) else "research"
        try:
            obj = make_example(text, domain, path.name)
            with DATASET.open("a", encoding="utf-8") as f:
                f.write(json.dumps(obj, ensure_ascii=False) + "\n")
            made += 1
        except Exception as exc:
            print(f"[KHUONG] skip {path.name}: {exc}")
    return made

def main():
    print(f"Khương worker: model={MODEL}, interval={INTERVAL}s")
    once = os.getenv("KHUONG_ONCE", "0") == "1"
    while True:
        n = ingest_local_files()
        print(f"[KHUONG] generated={n}")
        if once:
            break
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
