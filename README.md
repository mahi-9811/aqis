# AQIS Monorepo

This repository is organized as a multi-language system with clear ownership boundaries:

- `aqis/`: existing Python domain package for parsing, OCR, feature extraction, and risk scoring
- `services/python_api/`: Python API wrapper around the AQIS package
- `services/java-gateway/`: Java Spring Boot gateway for orchestration and enterprise integrations
- `apps/web/`: JavaScript React frontend for uploads, prediction requests, and result visualization

## Recommended responsibilities

- Python owns test artifact parsing, OCR, feature extraction, history loading, and prediction
- Java owns orchestration, authentication, persistence/integration, and enterprise workflows
- JavaScript owns the browser UI

## Supported request flow

1. The browser uploads `log.xml`, `STARTLog.txt`, and an optional screenshot in `apps/web`
2. The Java gateway receives the multipart request and applies platform concerns
3. The Java gateway forwards the files to the Python API
4. The Python API parses artifacts, stores the normalized bundle, and returns the analysis payload

## Run with Docker Compose

```bash
docker compose up --build
```

Services:

- Web UI: `http://localhost:5173`
- Java gateway: `http://localhost:8080`
- Python API: `http://localhost:8000`

In both local dev and Docker Compose, the web app uses the Java gateway as its default backend path:

- Browser -> `/api/predictions/...`
- Vite dev proxy -> `http://localhost:8080`
- Nginx in the web container -> `http://java-gateway:8080`

## Key endpoints

- Web app default lookup: `GET /api/predictions/{testName}`
- Web app default upload: `POST /api/predictions/upload`
- Java gateway lookup: `GET /api/predictions/{testName}`
- Java gateway upload: `POST /api/predictions/upload`
- Python lookup: `GET /predict/{test_name}`
- Python upload analysis: `POST /analyze`

## Current status

- The Python domain package and tests are working
- The FastAPI app now lives under `services/python_api`
- The Java gateway is the supported backend entry point for the web app
- The Java gateway forwards both lookup and upload-driven analysis requests
- The React app defaults to the gateway path in both Vite dev and Docker Compose
- Docker Compose is included for all three services

## Python tests

```bash
./.venv/bin/pytest -q
```
