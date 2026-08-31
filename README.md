# Khương

Lightweight AI agent for building high-quality training data on a small VPS.

## Architecture

Khương is intentionally **hybrid**:

- **Local AI:** small Qwen model via Ollama for inexpensive extraction and draft generation.
- **Orchestrator:** deterministic Python code owns files, provenance, validation and scheduling.
- **Strong model:** optional later; set `KHUONG_MODEL` to a compatible Ollama model or replace the model adapter.
- **Dataset:** JSONL with source and quality metadata.

The VPS therefore does not need a large local model. A stronger model can be added only when its quality/cost benefit justifies it.

## Current status

Implemented:
- one-command VPS bootstrap
- automatic small-model selection
- persistent user-level worker
- local raw-data directory
- JSONL dataset generation
- basic schema validation
- Vietnamese system behavior

Not yet enabled by default:
- uncontrolled web crawling
- automatic PDF ingestion
- automatic GitHub scraping
- model fine-tuning

Those stages need provenance, license filtering, deduplication and verification first.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/huyenytmk2912/1/main/install.sh | bash
```

## Data flow

```text
source
  ↓
raw
  ↓
extract
  ↓
generate
  ↓
validate
  ↓
data/dataset.jsonl
  ↓
quality gate
  ↓
train/validation/test
```

## Why this design

Running three large local models on a small VPS is usually the wrong bottleneck: RAM/VRAM and inference latency dominate. Separating orchestration from inference lets Khương stay small while preserving a path to stronger models.

The existing web dashboard remains a separate interface layer; the worker does not depend on it.
