# 1 — Autonomous Data Factory

`1` is the **VPS-1 data-preparation system**. It does not train models. A separate VPS is responsible for GPU training.

## Mission

Continuously discover useful public material and existing training-ready datasets for **deep reasoning, coding, and trading**, then turn accepted material into versioned, auditable training data.

## VPS split

```text
VPS 1 (repo 1)
  discover → import → extract → clean → dedup → classify
  → generate/transform → quality gate → train/val/test → export
                                                        │
                                                        ▼
VPS 2 (training)
  preflight → LoRA/QLoRA → evaluation → checkpoint
```

## Local AI

VPS 1 uses **llama.cpp directly with GGUF**. **Ollama is not used.**

Default local model:

```text
ggml-org/Qwen3-1.7B-GGUF:Q4_K_M
```

The installer validates all of the following before reporting success:

1. `llama-server` starts and its shared libraries resolve.
2. The HTTP runtime becomes healthy.
3. `/v1/models` reports the **exact configured model ID**.
4. A real Vietnamese inference smoke test returns `OK`.
5. Repository Python entrypoints pass `py_compile`.

If a check fails, installation stops instead of claiming success.

The factory remains usable for collection, import, cleaning, provenance and dataset assembly without model generation. VPS-1 never performs GPU training.

## Prefer existing good data

If an input dataset already has a compatible training schema, the importer keeps it rather than unnecessarily rewriting it. Every imported record is marked for provenance/quality review.

## Safety gates

The factory does **not** assume that publicly reachable material is training-licensed. It records source and license status and keeps ambiguous material reviewable. Synthetic examples are not accepted merely because they are valid JSON.

For reasoning, examples should teach problem solving with concise approaches, key steps and verification rather than storing hidden chain-of-thought. Coding data should eventually pass executable tests. Trading data should emphasize concepts, statistics, risk, market structure, backtesting and scenario analysis and must not fabricate returns.

## One-command VPS-1 install

```bash
rm -rf ~/training-data-agent && curl -fsSL https://raw.githubusercontent.com/huyenytmk2912/1/main/install.sh | bash
```

For a non-root account, use `sudo` as needed. The installer creates a clean VPS-1 project, installs the Python dependencies and llama.cpp runtime, downloads the configured GGUF model through llama.cpp, validates Vietnamese inference, and writes the runtime launcher. It does **not** install or start Ollama and does **not** start GPU training.

## Main commands

```bash
~/training-data-agent/run.sh status
~/training-data-agent/run.sh worker
~/training-data-agent/run.sh build
~/training-data-agent/run.sh readiness
~/training-data-agent/run.sh export
```

## Data layout

```text
data/
├── inbox/       optional user-provided datasets/documents
├── raw/         collected source records + provenance
├── dataset/     generated train/validation/test JSONL
├── review/      material awaiting review
├── export/      packages for VPS 2
└── logs/        runtime logs
```

## Current boundary

VPS 1 is intentionally responsible for **data**, not model training. The training server should consume the exported artifact and perform GPU work independently.
