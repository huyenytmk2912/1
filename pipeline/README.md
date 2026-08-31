# Pipeline modules

The project is deliberately split into stages so each stage can be replaced without rewriting the whole system.

- `collector.py`: discover and ingest public source metadata/content.
- `normalize.py`: normalize source records and remove duplicates.
- `generate.py`: optional local-LLM transformation into training examples.
- `verify.py`: deterministic quality gates and review queue.
- `dataset.py`: source-grouped train/validation/test build and reports.

The current v1 implementation is conservative: source licensing is recorded, but an unknown license is never silently treated as training-permitted.
