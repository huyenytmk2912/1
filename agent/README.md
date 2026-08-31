# Khương Agent

Khương uses a **hybrid architecture** rather than forcing every task through a large local model.

- A small local Qwen model handles cheap extraction, normalization and draft generation.
- The orchestrator keeps provenance and quality gates outside the model.
- A future stronger model can be selected with `KHUONG_MODEL` without changing the pipeline.
- The dataset is JSONL and every record keeps its source and quality notes.

## Pipeline

`source -> raw -> extraction -> generation -> validation -> dataset.jsonl`

Only files explicitly placed in `data/raw/*.txt` are processed by the current worker. This deliberately avoids uncontrolled web crawling and accidental copyright/licensed-data ingestion.

## Run once

```bash
KHUONG_ONCE=1 python3 agent/agent.py
```

## Continuous worker

Use `agent/khuong-worker.service` with a user-level systemd service.

## Next stages

1. Add source adapters (web/PDF/GitHub) with provenance and license metadata.
2. Add deduplication and contamination checks.
3. Add a verifier model or deterministic tests for coding samples.
4. Export train/validation/test splits.
5. Fine-tune only after dataset quality is measured.
