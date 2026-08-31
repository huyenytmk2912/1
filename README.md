# 1 — Autonomous Training Data Agent

Independent project for building training datasets for **deep reasoning, coding and trading**.

## Goal

The system continuously discovers suitable public sources, records provenance, extracts/normalizes material, reuses data that is already in a usable training format when possible, generates structured examples when needed, validates them, removes duplicates, and produces train/validation/test splits.

## Architecture

```text
public sources / existing datasets
            ↓
       source discovery
            ↓
 provenance + source policy
            ↓
       ingest / extract
            ↓
 normalize + deduplicate
            ↓
 ┌──────────┬──────────┬──────────┐
 reasoning   coding    trading
 └──────────┴──────────┴──────────┘
            ↓
   generate / transform
            ↓
      quality validation
            ↓
 train / validation / test
```

## Local AI is optional

The pipeline does **not** require a local model for source collection and organization. If Ollama + a small Qwen model are installed, the model is used for structured example generation. Without a model, the deterministic fallback still collects and prepares data, while generated records are marked for review.

This is deliberate: a small VPS should not be blocked by inference requirements.

## Domains

- **Reasoning:** logic, mathematics, scientific problem solving, multi-step analysis and verification.
- **Coding:** algorithms, programming, debugging, code review and software-engineering tasks. Future coding records should be checked with executable tests where possible.
- **Trading:** market structure, statistics, econometrics, portfolio/risk, backtesting and scenario analysis. The dataset must not fabricate performance or turn training examples into personalized financial advice.

## One-command fresh VPS

```bash
curl -fsSL https://raw.githubusercontent.com/huyenytmk2912/1/main/install.sh | bash
```

The installer prepares a Linux VPS, starts the persistent worker, and optionally installs a small local model when RAM is sufficient.

## Output

```text
data/raw/          collected source records
data/dataset/      validated JSONL datasets
data/logs/         runtime logs
data/state/        persistent state
```

The main output is `data/dataset/all.jsonl` plus deterministic `train.jsonl`, `validation.jsonl`, `test.jsonl`, and `stats.json`.

## Important quality policy

Publicly accessible does not automatically mean training-licensed. The system keeps source URLs/provenance and is intentionally conservative about arbitrary web crawling. Before redistribution or commercial training, licensing must be reviewed.

Synthetic data is also not automatically correct. High-value datasets should use stronger verification, source-level deduplication, contamination checks, and executable evaluation for coding tasks before fine-tuning.

## Status

The bootstrap and autonomous first-stage pipeline are ready to start. The next quality upgrades are additional source adapters, license metadata, stronger verification, richer existing-dataset importers, and a separate fine-tuning pipeline.
