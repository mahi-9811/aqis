# Java Gateway

Spring Boot service that fronts the Python predictor and is the right place for:

- authentication and authorization
- persistence to enterprise databases
- workflow orchestration and scheduling
- message queue integrations
- audit logging

## Run

```bash
mvn spring-boot:run
```

By default it calls the Python API at `http://localhost:8000`.

Configuration:

- `AQIS_PYTHON_BASE_URL`: Python API base URL, default `http://localhost:8000`
- `AQIS_GATEWAY_AUTH_ENABLED`: enable gateway API-key checks, default `false`
- `AQIS_GATEWAY_AUTH_HEADER`: API-key header name, default `X-AQIS-API-Key`
- `AQIS_GATEWAY_API_KEY`: expected API key when gateway auth is enabled

Endpoints:

- `GET /api/predictions/{testName}`
- `POST /api/predictions/upload`
