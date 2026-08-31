# 1 — Autonomous Training Data Agent

Independent project for building training datasets for **deep reasoning, coding and trading**.

## Goal

The system discovers public sources and existing datasets, records provenance, ingests material, normalizes it, reuses compatible training-format data when possible, generates structured examples when needed, validates them, deduplicates them, and produces train/validation/test splits.

## Pipeline

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

The deterministic pipeline can collect and organize data without a local model. If `MODEL` points to an Ollama model, it is used to generate structured examples. This keeps the project usable on a small VPS and allows a stronger model/API to be introduced later without redesigning the pipeline.

## Domains

- **Reasoning:** logic, mathematics, scientific problem solving, multi-step analysis and verification. Generated records should use concise key steps rather than hidden chain-of-thought.
- **Coding:** algorithms, programming, debugging, code review and software-engineering tasks. The roadmap includes executable tests before accepting generated coding records.
- **Trading:** market structure, statistics, econometrics, portfolio/risk, backtesting and scenario analysis. Do not fabricate performance or convert examples into personalized financial advice.

## One-command fresh VPS

```bash
curl -fsSL https://raw.githubusercontent.com/huyenytmk2912/1/main/install.sh | bash
```

The installer prepares a Linux VPS, starts the persistent worker, and uses a small local model only when the machine has enough RAM and the model can be installed successfully.

## Output

```text
data/raw/          collected source records + provenance
data/dataset/      validated JSONL datasets
data/logs/         runtime logs
data/state/        persistent state
```

Main outputs: `all.jsonl`, `train.jsonl`, `validation.jsonl`, `test.jsonl`, and `stats.json`.

## Quality and licensing

Publicly accessible does not automatically mean training-licensed. The system records source/provenance and is conservative about arbitrary crawling. License status must be reviewed before redistribution or commercial training.

Synthetic data is not automatically correct. Stronger verification, source-level deduplication, contamination checks, and executable evaluation for coding should be added as the project scales.

## Current status

The bootstrap and autonomous first-stage pipeline are ready to start. The next upgrades are richer source adapters, license metadata/scoring, stronger verification, existing-dataset importers, coding execution tests, and a separate fine-tuning pipeline.
