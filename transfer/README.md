# VPS 1 → VPS 2 transfer

Run `export/export_dataset.py` after the readiness gate passes.

The resulting artifact is accompanied by `manifest.json` and a SHA-256 file. Transfer it over SSH/SFTP to VPS 2; never commit datasets, credentials, or model weights to this repository.

Recommended verification on VPS 2:

```bash
sha256sum -c dataset.tar.gz.sha256
```

Then verify each member against `manifest.json` before training.
