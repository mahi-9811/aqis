# Architecture

## Language split

### Python

Python remains the decision engine because the existing code already contains:

- parsers for XML, start logs, and OCR
- feature extraction
- trend analysis
- rule-based scoring
- file-backed run history

### Java

Java should own integration-heavy concerns:

- security
- request validation beyond raw prediction
- persistence to relational databases
- scheduling and workflow execution
- messaging and downstream enterprise connectors

### JavaScript

JavaScript should own:

- operator workflows
- file upload UX
- prediction dashboards
- trend and failure explanation views

## Why this split works

- The ML and parsing domain does not need to be duplicated across languages
- The browser app stays focused on UX
- The Java service becomes the stable boundary for enterprise consumers

## Migration path

1. Keep existing AQIS Python logic in place
2. Run `services/python_api` as the first service
3. Point `services/java-gateway` to the Python API for both lookup and multipart upload
4. Point `apps/web` to the Java gateway as the only default browser-facing backend
5. In local dev, proxy `/api` from Vite to `http://localhost:8080`
6. In containerized runs, proxy `/api` from nginx in `apps/web` to `http://java-gateway:8080`
7. Later move persistence and workflow concerns into the Java service
