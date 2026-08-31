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

Optional on VPS 1. A small Ollama model can generate/transform examples when configured. The factory remains usable without it for collection, import, cleaning, provenance and dataset assembly.

## Prefer existing good data

If an input dataset already has a compatible training schema, the importer keeps it rather than unnecessarily rewriting it. Every imported record is marked for provenance/quality review.

## Safety gates

The factory does **not** assume that publicly reachable material is training-licensed. It records source and license status and keeps ambiguous material reviewable. Synthetic examples are not accepted merely because they are valid JSON.

For reasoning, examples should teach problem solving with concise approaches, key steps and verification rather than storing hidden chain-of-thought. Coding data should eventually pass executable tests. Trading data should emphasize concepts, statistics, risk, market structure, backtesting and scenario analysis and must not fabricate returns.

## One-command VPS-1 install

```bash
curl -fsSL https://raw.githubusercontent.com/huyenytmk2912/1/main/install.sh | bash
```

The installer creates the data-factory directories and optional local-AI runtime. It does **not** start GPU training.

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

The next production upgrades are richer source adapters, robust PDF/HTML extraction, explicit license metadata, stronger AI verification, coding sandbox tests, contamination detection, dataset versioning, and a secure transfer protocol to VPS 2.
