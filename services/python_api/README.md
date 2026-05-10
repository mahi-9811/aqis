# Python API

Thin wrapper around the shared `aqis` package.

## Run

```bash
PYTHONPATH=. ./.venv/bin/uvicorn services.python_api.main:app --reload
```

This service is the system of record for:

- parsing test artifacts
- OCR extraction
- feature extraction
- trend analysis
- risk prediction
- artifact upload ingestion
